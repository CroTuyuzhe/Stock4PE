import yfinance as yf
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go

# 定义要跟踪的指数
indices = {
    "沪深300": "000300.SS",   # 沪深300指数
    "纳斯达克综合": "^IXIC",   # 纳斯达克综合指数
    "标普500": "^GSPC",       # 标普500指数
    "恒生指数": "^HSI"         # 恒生指数
}

# 初始化 Dash 应用
app = Dash(__name__)
server = app.server  # 部署需要

app.layout = html.Div([
    html.H1("📊 全球主要股指实时看板", style={'textAlign': 'center'}),

    dcc.Interval(
        id='interval-component',
        interval=60*1000,  # 每60秒刷新一次
        n_intervals=0
    ),

    dcc.Graph(id='live-update-graph'),

])

@app.callback(
    Output('live-update-graph', 'figure'),
    [Input('interval-component', 'n_intervals')]
)
def update_graph(n):
    traces = []

    for name, ticker in indices.items():
        data = yf.download(ticker, period="5d", interval="30m")
        traces.append(go.Scatter(
            x=data.index,
            y=data['Close'],
            mode='lines',
            name=name
        ))

    figure = {
        'data': traces,
        'layout': go.Layout(
            title="全球股指走势 (过去5天, 30分钟更新)",
            xaxis=dict(title='时间'),
            yaxis=dict(title='指数点位'),
            hovermode='x unified'
        )
    }
    return figure

if __name__ == '__main__':
    app.run_server(debug=True)
