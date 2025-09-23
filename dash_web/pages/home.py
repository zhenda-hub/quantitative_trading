from dash import dcc, html
import plotly.graph_objects as go
import pandas as pd
import dash
import dash_bootstrap_components as dbc

dash.register_page(__name__, path='/', folder='')

# 模拟数据 - 在实际应用中可以从数据库或API获取
market_data = {
    'total_assets': '1,234.56M',
    'daily_change': '+2.34%',
    'portfolio_value': '987.65M',
    'active_strategies': '15'
}


# 从CSV文件读取最新新闻数据
def get_latest_news():
    
    # title link summary
    df_news = pd.read_csv("datas/raw/news/ak_stock_info_global_ths.csv")
    df_news = df_news.rename(columns={'内容': 'summary', '标题': 'title', '链接': 'link', '发布时间': 'time'})
    df_news2 = pd.read_csv("datas/raw/news/ak_stock_info_global_em.csv")
    df_news2 = df_news2.rename(columns={'摘要': 'summary', '标题': 'title', '链接': 'link', '发布时间': 'time'})
    # 合并两个数据源
    df_news = pd.concat([df_news, df_news2], ignore_index=True)
    
    df_news = df_news.drop_duplicates(subset=['title'])
    
    # 随机展示20条
    df_news = df_news.sample(n=20, random_state=1)
    # df_news = df_news.sort_values(by='time', ascending=False)
    
    # 'title', 'summary', 'time', 'link'
    news_list = df_news.to_dict('records')
    
    return news_list


layout = dbc.Container([
    # 欢迎区域
    dbc.Row([
        dbc.Col([
            html.Div([
                html.H1(
                    '量化交易仪表板',
                    className='text-center mb-3',
                    style={'color': '#2E86AB', 'fontWeight': 'bold'}
                ),
                html.P(
                    '专业的量化投资分析与决策平台',
                    className='text-center text-muted lead mb-4'
                )
            ], className='py-5', style={'backgroundColor': '#f8f9fa'})
        ], width=12)
    ]),
    
    # 实时数据概览区域
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader('📊 实时市场概览'),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                html.H5('主要指数', className='text-primary'),
                                html.Div([
                                    html.Span('上证指数: ', className='fw-bold'),
                                    html.Span('3,245.67', className='text-success'),
                                    html.Small(' +1.23%', className='text-success ms-2')
                                ], className='mb-1'),
                                html.Div([
                                    html.Span('深证成指: ', className='fw-bold'),
                                    html.Span('11,234.56', className='text-success'),
                                    html.Small(' +0.89%', className='text-success ms-2')
                                ], className='mb-1'),
                                html.Div([
                                    html.Span('创业板指: ', className='fw-bold'),
                                    html.Span('2,345.78', className='text-danger'),
                                    html.Small(' -0.45%', className='text-danger ms-2')
                                ])
                            ])
                        ], md=4),
                        dbc.Col([
                            html.Div([
                                html.H5('商品期货', className='text-info'),
                                html.Div([
                                    html.Span('黄金: ', className='fw-bold'),
                                    html.Span('2,045.50', className='text-success'),
                                    html.Small(' +0.78%', className='text-success ms-2')
                                ], className='mb-1'),
                                html.Div([
                                    html.Span('原油: ', className='fw-bold'),
                                    html.Span('85.23', className='text-success'),
                                    html.Small(' +2.15%', className='text-success ms-2')
                                ], className='mb-1'),
                                html.Div([
                                    html.Span('铜: ', className='fw-bold'),
                                    html.Span('8,456.00', className='text-danger'),
                                    html.Small(' -0.32%', className='text-danger ms-2')
                                ])
                            ])
                        ], md=4),
                        dbc.Col([
                            html.Div([
                                html.H5('外汇市场', className='text-warning'),
                                html.Div([
                                    html.Span('USD/CNY: ', className='fw-bold'),
                                    html.Span('7.2456', className='text-success'),
                                    html.Small(' +0.12%', className='text-success ms-2')
                                ], className='mb-1'),
                                html.Div([
                                    html.Span('EUR/USD: ', className='fw-bold'),
                                    html.Span('1.0854', className='text-danger'),
                                    html.Small(' -0.08%', className='text-danger ms-2')
                                ], className='mb-1'),
                                html.Div([
                                    html.Span('GBP/USD: ', className='fw-bold'),
                                    html.Span('1.2654', className='text-success'),
                                    html.Small(' +0.15%', className='text-success ms-2')
                                ])
                            ])
                        ], md=4)
                    ]),
                    # html.Hr(),
                    # dbc.Row([
                    #     dbc.Col([
                    #         html.Div([
                    #             html.H6('今日交易统计', className='text-center'),
                    #             html.Div([
                    #                 html.H4('156', className='text-center text-primary mb-0'),
                    #                 html.Small('成交笔数', className='text-muted d-block text-center')
                    #             ])
                    #         ])
                    #     ], md=3),
                    #     dbc.Col([
                    #         html.Div([
                    #             html.H6('持仓市值', className='text-center'),
                    #             html.Div([
                    #                 html.H4('876.5M', className='text-center text-success mb-0'),
                    #                 html.Small('当前估值', className='text-muted d-block text-center')
                    #             ])
                    #         ])
                    #     ], md=3),
                    #     dbc.Col([
                    #         html.Div([
                    #             html.H6('收益率', className='text-center'),
                    #             html.Div([
                    #                 html.H4('+8.76%', className='text-center text-info mb-0'),
                    #                 html.Small('本月累计', className='text-muted d-block text-center')
                    #             ])
                    #         ])
                    #     ], md=3),
                    #     dbc.Col([
                    #         html.Div([
                    #             html.H6('风险指标', className='text-center'),
                    #             html.Div([
                    #                 html.H4('0.23', className='text-center text-warning mb-0'),
                    #                 html.Small('夏普比率', className='text-muted d-block text-center')
                    #             ])
                    #         ])
                    #     ], md=3)
                    # ])
                ])
            ], className='border-0 shadow-sm',
               style={'transition': 'transform 0.2s ease-in-out'})
        ], width=12, className='mb-4')
    ]),
    
    # 图表预览和功能导航
    dbc.Row([
        # 最新新闻 - 扩大区域
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.H4('📰 最新市场新闻', className='mb-0'),
                    # html.Small('实时更新', className='text-muted')
                ]),
                dbc.CardBody([
                    html.Div([
                        html.Div([
                            html.Div([
                                html.A(
                                    html.H5(news['title'], className='mb-1'),
                                    href=news['link'],
                                    target='_blank',
                                    style={'textDecoration': 'none', 'color': 'inherit'}
                                ),
                                html.P(news['summary'], className='text-muted small mb-1'),
                                html.Small(news['time'], className='text-muted')
                            ])
                        ], className='border-bottom pb-3 mb-3')
                        for news in get_latest_news()
                    ], style={'maxHeight': '400px', 'overflowY': 'auto', 'padding': '10px'})
                ])
            ], className='h-100 border-0 shadow-sm',
               style={'transition': 'transform 0.2s ease-in-out', 'minHeight': '450px'})
        ], md=8, className='mb-3'),  # 从md=6改为md=8，占据更多空间
        
        # 快速导航 - 缩小区域
        dbc.Col([
            dbc.Card([
                dbc.CardHeader('🚀 快速导航'),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Button(
                                '📈 指数分析', color='primary',
                                href='/index', className='w-100 mb-2', size='sm'
                            ),
                            dbc.Button(
                                '💰 金属市场', color='success',
                                href='/metals', className='w-100 mb-2', size='sm'
                            ),
                            dbc.Button(
                                '🏢 行业分析', color='info',
                                href='/industry', className='w-100 mb-2', size='sm'
                            ),
                            dbc.Button(
                                '📊 虚拟资产', color='warning',
                                href='/virtual', className='w-100 mb-2', size='sm'
                            )
                        ], width=12)
                    ])
                ])
            ], className='h-100 border-0 shadow-sm',
               style={'transition': 'transform 0.2s ease-in-out'})
        ], md=4, className='mb-3')  # 从md=6改为md=4，缩小空间
    ]),
    
    
], fluid=True, className='py-4', style={'backgroundColor': '#f8f9fa'})
