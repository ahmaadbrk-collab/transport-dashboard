from flask import Flask, render_template_string
import pandas as pd
import plotly.express as px

app = Flask(__name__)

# قراءة البيانات من CSV
df = pd.read_csv('trips_data.csv')

@app.route('/')
def dashboard():
    total_trips = len(df)
    total_revenue = df['Revenue'].sum()
    total_profit = df['Profit'].sum()
    profit_margin = (total_profit / total_revenue * 100)
    
    top_dest = df.groupby('FromPos')['Profit'].sum().nlargest(10).reset_index()
    fig1 = px.bar(top_dest, x='Profit', y='FromPos', orientation='h', title='أفضل 10 وجهات')
    graph1_html = fig1.to_html(full_html=False)
    
    driver_stats = df.groupby('DriverName').agg({'Profit': ['sum', 'mean', 'count']}).reset_index()
    driver_stats.columns = ['DriverName', 'TotalProfit', 'AvgProfit', 'TripCount']
    driver_stats = driver_stats[driver_stats['TripCount'] >= 5]
    top_drv = driver_stats.nlargest(10, 'AvgProfit')
    fig2 = px.bar(top_drv, x='AvgProfit', y='DriverName', orientation='h', title='أفضل 10 سائقين')
    graph2_html = fig2.to_html(full_html=False)
    
    html = f'''
    <!DOCTYPE html>
    <html dir="rtl">
    <head>
        <title>لوحة معلومات النقليات</title>
        <style>
            body {{ font-family: Arial; margin: 20px; background: #f5f5f5; }}
            .kpi {{ display: flex; justify-content: space-around; margin: 20px 0; }}
            .kpi-card {{ background: white; padding: 20px; border-radius: 10px; text-align: center; flex: 1; margin: 10px; }}
            .kpi-value {{ font-size: 32px; font-weight: bold; color: #3498db; }}
        </style>
    </head>
    <body>
        <h1>لوحة معلومات النقليات</h1>
        <div class="kpi">
            <div class="kpi-card">
                <div class="kpi-value">{total_trips:,}</div>
                <div>عدد الرحلات</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value">{total_revenue:,.0f}</div>
                <div>الإيرادات</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value">{total_profit:,.0f}</div>
                <div>الأرباح</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value">{profit_margin:.1f}%</div>
                <div>هامش الربح</div>
            </div>
        </div>
        {graph1_html}
        {graph2_html}
    </body>
    </html>
    '''
    return render_template_string(html)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)