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


# 模拟最新新闻数据
def get_latest_news():
    return [
        {
            'title': '美联储维持利率不变，市场反应积极',
            'time': '2小时前',
            'source': '财经新闻',
            'impact': '积极',
            'summary': '美联储宣布维持基准利率在5.25%-5.50%区间不变，符合市场预期。'
        },
        {
            'title': '科技股财报季来临，投资者密切关注',
            'time': '5小时前', 
            'source': '华尔街日报',
            'impact': '中性',
            'summary': '苹果、微软等科技巨头即将发布季度财报，市场预期乐观。'
        },
        {
            'title': '原油价格突破关键阻力位',
            'time': '昨天',
            'source': '能源资讯',
            'impact': '积极',
            'summary': '布伦特原油价格突破85美元/桶，创近三个月新高。'
        },
        {
            'title': '新兴市场货币波动加剧',
            'time': '昨天',
            'source': '外汇观察',
            'impact': '谨慎',
            'summary': '受美元走强影响，新兴市场货币普遍承压。'
        },
        {
            'title': '人工智能板块持续走强',
            'time': '前天',
            'source': '科技前沿',
            'impact': '积极',
            'summary': 'AI相关股票连续上涨，机构看好长期发展前景。'
        },
        {
            'title': '房地产市场政策调整',
            'time': '3天前',
            'source': '地产观察',
            'impact': '中性',
            'summary': '多地出台房地产支持政策，市场预期逐步回暖。'
        },
        {
            'title': '黄金价格创历史新高',
            'time': '4天前',
            'source': '贵金属分析',
            'impact': '积极',
            'summary': '避险情绪推动黄金价格突破2100美元/盎司。'
        },
        {
            'title': '电动汽车销量增长放缓',
            'time': '5天前',
            'source': '汽车行业',
            'impact': '谨慎',
            'summary': '全球电动汽车销量增速放缓，市场竞争加剧。'
        }
    ]


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
                                html.H5(news['title'], className='mb-1'),
                                html.P(news['summary'], className='text-muted small mb-2'),
                                html.Div([
                                    html.Small(f"{news['time']} | {news['source']}", 
                                             className='text-muted'),
                                    html.Span(f" {news['impact']}", 
                                            className=f"badge bg-{'success' if news['impact'] == '积极' else 'warning' if news['impact'] == '谨慎' else 'info'} ms-2")
                                ], className='d-flex justify-content-between align-items-center')
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
