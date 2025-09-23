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
            'impact': '积极'
        },
        {
            'title': '科技股财报季来临，投资者密切关注',
            'time': '5小时前', 
            'source': '华尔街日报',
            'impact': '中性'
        },
        {
            'title': '原油价格突破关键阻力位',
            'time': '昨天',
            'source': '能源资讯',
            'impact': '积极'
        },
        {
            'title': '新兴市场货币波动加剧',
            'time': '昨天',
            'source': '外汇观察',
            'impact': '谨慎'
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
    
    # 关键指标卡片
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4('总资产规模', className='card-title'),
                    html.H3(market_data['total_assets'], 
                           className='text-primary'),
                    html.Small('USD', className='text-muted')
                ])
            ], className='text-center h-100 border-0 shadow-sm',
               style={'transition': 'transform 0.2s ease-in-out'})
        ], md=3, className='mb-3'),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4('日变化率', className='card-title'),
                    html.H3(
                        market_data['daily_change'],
                        className='text-success' if '+' in 
                        market_data['daily_change'] else 'text-danger'
                    ),
                    html.Small('今日表现', className='text-muted')
                ])
            ], className='text-center h-100 border-0 shadow-sm',
               style={'transition': 'transform 0.2s ease-in-out'})
        ], md=3, className='mb-3'),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4('投资组合价值', className='card-title'),
                    html.H3(market_data['portfolio_value'], 
                           className='text-info'),
                    html.Small('当前估值', className='text-muted')
                ])
            ], className='text-center h-100 border-0 shadow-sm',
               style={'transition': 'transform 0.2s ease-in-out'})
        ], md=3, className='mb-3'),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4('活跃策略', className='card-title'),
                    html.H3(market_data['active_strategies'], 
                           className='text-warning'),
                    html.Small('运行中', className='text-muted')
                ])
            ], className='text-center h-100 border-0 shadow-sm',
               style={'transition': 'transform 0.2s ease-in-out'})
        ], md=3, className='mb-3')
    ], className='mb-4'),
    
    # 图表预览和功能导航
    dbc.Row([
        # 最新新闻
        dbc.Col([
            dbc.Card([
                dbc.CardHeader('最新市场新闻'),
                dbc.CardBody([
                    html.Div([
                        html.Div([
                            html.H6(news['title'], className='mb-1'),
                            html.Small(f"{news['time']} | {news['source']}", 
                                     className='text-muted'),
                            html.Span(f" {news['impact']}", 
                                    className=f"badge bg-{'success' if news['impact'] == '积极' else 'warning' if news['impact'] == '谨慎' else 'info'} float-end")
                        ], className='border-bottom pb-2 mb-2')
                        for news in get_latest_news()
                    ], style={'maxHeight': '200px', 'overflowY': 'auto'})
                ])
            ], className='h-100 border-0 shadow-sm',
               style={'transition': 'transform 0.2s ease-in-out'})
        ], md=6, className='mb-3'),
        
        # 快速导航
        dbc.Col([
            dbc.Card([
                dbc.CardHeader('快速导航'),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Button(
                                '📈 指数分析', color='primary',
                                href='/index', className='w-100 mb-2'
                            ),
                            dbc.Button(
                                '💰 金属市场', color='success',
                                href='/metals', className='w-100 mb-2'
                            )
                        ], md=6),
                        dbc.Col([
                            dbc.Button(
                                '🏢 行业分析', color='info',
                                href='/industry', className='w-100 mb-2'
                            ),
                            dbc.Button(
                                '📊 虚拟资产', color='warning',
                                href='/virtual', className='w-100 mb-2'
                            )
                        ], md=6)
                    ])
                ])
            ], className='h-100 border-0 shadow-sm',
               style={'transition': 'transform 0.2s ease-in-out'})
        ], md=6, className='mb-3')
    ]),
    
    # 功能简介区域
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4('平台功能', className='mb-3'),
                    html.Ul([
                        html.Li('多市场实时数据监控'),
                        html.Li('量化策略回测与分析'),
                        html.Li('投资组合风险管理'),
                        html.Li('自动化交易执行')
                    ], className='list-unstyled'),
                    html.P(
                        '基于先进的数据分析和机器学习技术，为投资决策提供科学依据。',
                        className='text-muted mt-3'
                    )
                ])
            ], className='border-0 shadow-sm',
               style={'transition': 'transform 0.2s ease-in-out'})
        ], width=12, className='mb-4')
    ])
], fluid=True, className='py-4', style={'backgroundColor': '#f8f9fa'})
