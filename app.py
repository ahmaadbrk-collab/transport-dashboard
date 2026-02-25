from flask import Flask, request
import pandas as pd
import plotly.graph_objects as go

app = Flask(__name__)

# قراءة البيانات
df = pd.read_csv('trips_data.csv')
df['TripDate'] = pd.to_datetime(df['TripDate'], errors='coerce')
df['Revenue'] = pd.to_numeric(df['Revenue'], errors='coerce').fillna(0)
df['Profit'] = pd.to_numeric(df['Profit'], errors='coerce').fillna(0)
df['MonthLabel'] = df['TripDate'].dt.strftime('%Y-%m')

@app.route('/')
def dashboard():
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    driver_filter = request.args.get('driver', 'all')
    from_city = request.args.get('from_city', 'all')
    to_city = request.args.get('to_city', 'all')

    filtered = df.copy()

    if date_from:
        filtered = filtered[filtered['TripDate'] >= pd.to_datetime(date_from)]
    if date_to:
        filtered = filtered[filtered['TripDate'] <= pd.to_datetime(date_to)]
    if driver_filter != 'all':
        filtered = filtered[filtered['DriverName'] == driver_filter]
    if from_city != 'all':
        filtered = filtered[filtered['FromPos'] == from_city]
    if to_city != 'all':
        filtered = filtered[filtered['ToPos'] == to_city]

    total_trips = len(filtered)
    total_revenue = filtered['Revenue'].sum()
    total_profit = filtered['Profit'].sum()
    profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0

    # أفضل 10 وجهات
    top_dest = filtered.groupby('FromPos')['Profit'].sum().nlargest(10).reset_index()
    fig1 = go.Figure(go.Bar(
        x=top_dest['Profit'], y=top_dest['FromPos'],
        orientation='h', marker_color='#3498db',
        text=top_dest['Profit'].apply(lambda x: f'{x:,.0f}'),
        textposition='outside'
    ))
    fig1.update_layout(
        title='أفضل 10 وجهات ربحاً',
        xaxis_title='الربح', yaxis_title='الوجهة',
        font=dict(family='Arial'), margin=dict(t=60),
        dragmode=False, hovermode=False
    )
    graph1_html = fig1.to_html(full_html=False, config={'staticPlot': True, 'displayModeBar': False})

    # أفضل 10 سائقين
    driver_stats = filtered.groupby('DriverName').agg({'Profit': ['sum', 'mean', 'count']}).reset_index()
    driver_stats.columns = ['DriverName', 'TotalProfit', 'AvgProfit', 'TripCount']
    driver_stats = driver_stats[driver_stats['TripCount'] >= 1]
    top_drv = driver_stats.nlargest(10, 'AvgProfit')
    fig2 = go.Figure(go.Bar(
        x=top_drv['AvgProfit'], y=top_drv['DriverName'],
        orientation='h', marker_color='#2ecc71',
        text=top_drv['AvgProfit'].apply(lambda x: f'{x:,.0f}'),
        textposition='outside'
    ))
    fig2.update_layout(
        title='أفضل 10 سائقين (متوسط الربح لكل رحلة)',
        xaxis_title='متوسط الربح', yaxis_title='السائق',
        font=dict(family='Arial'), margin=dict(t=60),
        dragmode=False, hovermode=False
    )
    graph2_html = fig2.to_html(full_html=False, config={'staticPlot': True, 'displayModeBar': False})

    # مقارنة شهرية
    monthly = filtered.groupby('MonthLabel').agg(
        الإيرادات=('Revenue', 'sum'),
        الأرباح=('Profit', 'sum')
    ).reset_index().sort_values('MonthLabel')

    fig3 = go.Figure()
    fig3.add_trace(go.Bar(name='الإيرادات', x=monthly['MonthLabel'], y=monthly['الإيرادات'], marker_color='#3498db'))
    fig3.add_trace(go.Bar(name='الأرباح', x=monthly['MonthLabel'], y=monthly['الأرباح'], marker_color='#2ecc71'))
    fig3.update_layout(
        title='المقارنة الشهرية للإيرادات والأرباح',
        barmode='group', xaxis_title='الشهر', yaxis_title='المبلغ',
        font=dict(family='Arial'), margin=dict(t=60),
        dragmode=False, hovermode=False
    )
    graph3_html = fig3.to_html(full_html=False, config={'staticPlot': True, 'displayModeBar': False})

    # التحليل النصي
    if not filtered.empty and not top_dest.empty and not driver_stats.empty:
        best_dest = top_dest.iloc[0]['FromPos']
        best_dest_val = top_dest.iloc[0]['Profit']
        best_driver = driver_stats.loc[driver_stats['AvgProfit'].idxmax(), 'DriverName']
        best_driver_val = driver_stats['AvgProfit'].max()
        best_driver_trips = driver_stats.loc[driver_stats['AvgProfit'].idxmax(), 'TripCount']

        analysis_html = f'''
        <div class="analysis">
            <div class="analysis-card">
                <div class="analysis-icon">🏆</div>
                <div class="analysis-text">
                    <strong>أفضل وجهة</strong>
                    <span class="analysis-branch">{best_dest}</span>
                    <span class="analysis-val">{best_dest_val:,.0f} ربح إجمالي</span>
                </div>
            </div>
            <div class="analysis-card">
                <div class="analysis-icon">🚗</div>
                <div class="analysis-text">
                    <strong>أفضل سائق</strong>
                    <span class="analysis-branch">{best_driver}</span>
                    <span class="analysis-val">{best_driver_val:,.0f} متوسط ربح / رحلة</span>
                    <span style="color:#7f8c8d; font-size:13px;">({int(best_driver_trips)} رحلة)</span>
                </div>
            </div>
            <div class="analysis-card">
                <div class="analysis-icon">📊</div>
                <div class="analysis-text">
                    <strong>هامش الربح الإجمالي</strong>
                    <span class="analysis-branch">للفترة المحددة</span>
                    <span class="analysis-val">{profit_margin:.1f}%</span>
                </div>
            </div>
        </div>
        '''
    else:
        analysis_html = '<p>لا توجد بيانات كافية للتحليل.</p>'

    # خيارات الفلاتر
    drivers = sorted(df['DriverName'].dropna().unique())
    driver_options = '<option value="all">كل السائقين</option>'
    for d in drivers:
        selected = 'selected' if driver_filter == d else ''
        driver_options += f'<option value="{d}" {selected}>{d}</option>'

    from_cities = sorted(df['FromPos'].dropna().unique())
    from_options = '<option value="all">كل المدن</option>'
    for c in from_cities:
        selected = 'selected' if from_city == c else ''
        from_options += f'<option value="{c}" {selected}>{c}</option>'

    to_cities = sorted(df['ToPos'].dropna().unique())
    to_options = '<option value="all">كل المدن</option>'
    for c in to_cities:
        selected = 'selected' if to_city == c else ''
        to_options += f'<option value="{c}" {selected}>{c}</option>'

    html = f'''
    <!DOCTYPE html>
    <html dir="rtl">
    <head>
        <title>لوحة معلومات النقليات</title>
        <style>
            body {{ font-family: Arial; margin: 20px; background: #f0f2f5; }}
            h1 {{ color: #2c3e50; text-align: center; margin-bottom: 20px; }}
            .filters {{ background: white; padding: 15px 20px; border-radius: 10px; margin-bottom: 20px; display: flex; gap: 15px; align-items: center; flex-wrap: wrap; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
            .filters label {{ font-weight: bold; color: #2c3e50; }}
            .filters select, .filters input {{ padding: 8px; border-radius: 5px; border: 1px solid #ccc; font-size: 14px; }}
            .filters button {{ padding: 8px 25px; background: #3498db; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 14px; font-weight: bold; }}
            .kpi {{ display: flex; justify-content: space-around; margin-bottom: 20px; flex-wrap: wrap; }}
            .kpi-card {{ background: white; padding: 20px 30px; border-radius: 10px; text-align: center; flex: 1; margin: 8px; min-width: 150px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
            .kpi-value {{ font-size: 28px; font-weight: bold; color: #3498db; }}
            .kpi-value.green {{ color: #2ecc71; }}
            .kpi-label {{ color: #7f8c8d; margin-top: 5px; }}
            .chart {{ background: white; border-radius: 10px; padding: 15px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
            .analysis {{ display: flex; gap: 15px; margin-bottom: 20px; flex-wrap: wrap; }}
            .analysis-card {{ background: white; border-radius: 10px; padding: 20px; flex: 1; min-width: 200px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); display: flex; align-items: center; gap: 15px; }}
            .analysis-icon {{ font-size: 36px; }}
            .analysis-text {{ display: flex; flex-direction: column; gap: 4px; font-size: 15px; }}
            .analysis-branch {{ color: #2c3e50; font-size: 18px; font-weight: bold; }}
            .analysis-val {{ color: #3498db; font-size: 18px; font-weight: bold; }}
        </style>
    </head>
    <body>
        <h1>لوحة معلومات النقليات</h1>

        <div class="filters">
            <form method="get" style="display:flex; gap:15px; align-items:center; flex-wrap:wrap;">
                <div>
                    <label>السائق: </label>
                    <select name="driver">{driver_options}</select>
                </div>
                <div>
                    <label>من مدينة: </label>
                    <select name="from_city">{from_options}</select>
                </div>
                <div>
                    <label>إلى مدينة: </label>
                    <select name="to_city">{to_options}</select>
                </div>
                <div>
                    <label>من تاريخ: </label>
                    <input type="date" name="date_from" value="{date_from}">
                </div>
                <div>
                    <label>إلى تاريخ: </label>
                    <input type="date" name="date_to" value="{date_to}">
                </div>
                <button type="submit">تطبيق</button>
            </form>
        </div>

        <div class="kpi">
            <div class="kpi-card">
                <div class="kpi-value">{total_trips:,}</div>
                <div class="kpi-label">عدد الرحلات</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value">{total_revenue:,.0f}</div>
                <div class="kpi-label">الإيرادات</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value green">{total_profit:,.0f}</div>
                <div class="kpi-label">الأرباح</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value">{profit_margin:.1f}%</div>
                <div class="kpi-label">هامش الربح</div>
            </div>
        </div>

        {analysis_html}

        <div class="chart">{graph3_html}</div>
        <div class="chart">{graph1_html}</div>
        <div class="chart">{graph2_html}</div>

    </body>
    </html>
    '''
    return html

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
