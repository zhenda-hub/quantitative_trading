from dash import Dash, dcc, html, Input, Output, callback
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import dash
from loguru import logger


dash.register_page(__name__)

df_glod = pd.read_csv("datas/raw/metals/macro_cons_gold.csv")
df_silver = pd.read_csv("datas/raw/metals/macro_cons_silver.csv")


# draw line
fig = go.Figure()
fig.add_trace(go.Scatter(x=df_glod['日期'], y=df_glod['单价'], mode='lines+markers', name='Gold'))
fig.add_trace(go.Scatter(x=df_silver['日期'], y=df_silver['单价'], mode='lines+markers', name='Silver'))
fig.update_layout(
    title='Gold and Silver Prices Over Time',
    xaxis_title='Date', 
    yaxis_title='Price (USD per Ounce)',
    legend_title='Metals',
    height=1000,
)
fig.update_xaxes(
    rangeslider_visible=True,  # 添加滑动块
    minor=dict(ticks="inside", showgrid=True),  # 辅助刻度
    # 范围选择器按钮
    rangeselector=dict(
        buttons=list([
            dict(count=1, label="1month", step="month", stepmode="backward"),
            dict(count=6, label="6month", step="month", stepmode="backward"),
            dict(count=1, label="1year", step="year", stepmode="backward"),
            dict(count=3, label="3year", step="year", stepmode="backward"),
            dict(count=5, label="5year", step="year", stepmode="backward"),
            dict(count=10, label="10year", step="year", stepmode="backward"),
            dict(count=20, label="20year", step="year", stepmode="backward"),
            dict(step="all")
        ])
    )
)




layout = html.Div(
    [
        html.H4("贵金属价格走势"),
        dcc.Graph(figure=fig,),
    ]
)