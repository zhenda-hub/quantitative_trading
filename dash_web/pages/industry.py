import dash
from dash import Dash, dcc, html, Input, Output, callback
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import dash_bootstrap_components as dbc

# 注册页面
dash.register_page(__name__, path='/industry')

# 读取数据
df = pd.read_csv("datas/raw/stocks/ef_行业板块.csv")
df['总市值'] = df['总市值'].astype(float)
df['涨跌幅'] = df['涨跌幅'].astype(float)

# 创建布局
layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("行业板块分析", className="text-center my-4")
        ])
    ]),
    
    dbc.Row([
        dbc.Col([
            dcc.Graph(
                id='industry-bubble-chart',
                figure=px.scatter(df, 
                                 x='涨跌幅', 
                                 y='总市值',
                                 size='总市值',
                                 color='涨跌幅',
                                 hover_name='股票名称',
                                 hover_data={'涨跌幅': ':.2f%', '总市值': ':,.0f'},
                                 title='行业板块市值与涨跌幅关系图',
                                 labels={'涨跌幅': '涨跌幅 (%)', '总市值': '总市值'},
                                 color_continuous_scale=['red', 'lightgrey', 'green'],
                                 color_continuous_midpoint=0)
                .update_layout(
                    xaxis_title='涨跌幅 (%)',
                    yaxis_title='总市值',
                    yaxis_type='log',
                    showlegend=False,
                    hovermode='closest'
                )
                .add_vline(x=0, line_width=1, line_dash="dash", line_color="gray")
            )
        ], width=12)
    ]),
    
    dbc.Row([
        dbc.Col([
            html.H3("行业涨跌幅排名", className="text-center my-4")
        ])
    ]),
    
    dbc.Row([
        dbc.Col([
            dcc.Graph(
                id='industry-bar-chart',
                figure=px.bar(df.sort_values('涨跌幅', ascending=False),
                             x='股票名称',
                             y='涨跌幅',
                             color='涨跌幅',
                             color_continuous_scale=['red', 'lightgrey', 'green'],
                             color_continuous_midpoint=0,
                             title='行业涨跌幅排名',
                             labels={'涨跌幅': '涨跌幅 (%)', '股票名称': '行业名称'})
                .update_layout(xaxis_tickangle=-45)
            )
        ], width=12)
    ]),
    dbc.Row([
        dbc.Col([
            html.H4("相关链接", className="text-center my-4"),
            dbc.Button("大盘云图", href="https://52etf.site/", 
                        external_link=True, target="_blank", color="primary"),
            # dbc.ButtonGroup([
            #     dbc.Button("东方财富", href="https://www.eastmoney.com", 
            #             external_link=True, target="_blank", color="primary"),
            #     dbc.Button("同花顺", href="https://www.10jqka.com.cn", 
            #             external_link=True, color="secondary"),
            #     dbc.Button("新浪财经", href="https://finance.sina.com.cn", 
            #             external_link=True, color="success")
            # ], className="me-3"),
            
            # dbc.ButtonGroup([
            #     dbc.Button("债券分析", href="/bond", color="info"),
            #     dbc.Button("首页", href="/", color="light"),
            #     dbc.Button("虚拟货币", href="/virtual", color="warning")
            # ])
        ], width=12, className="text-center")
    ]),
], fluid=True)
