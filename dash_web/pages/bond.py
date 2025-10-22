from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from dash import Dash, dcc, html, Input, Output, callback, dash_table
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import dash

from loguru import logger

# TODO: 12天，更新一次数据

def judge_bonds(df: pd.DataFrame):
    avg_low = df['双低'].mean()
    msg1 = f"转股溢价率平均值： {df['转股溢价率'].mean():.2f}, 双低平均值： {avg_low:.2f}"
    msg2 = f"转股溢价率中位数： {df['转股溢价率'].median():.2f}, 双低中位数： {df['双低'].median():.2f}"
    logger.info(msg1)
    logger.info(msg2)

    res = ''
    if avg_low < 150:
        res = '100%仓位'
    elif avg_low < 155:
        res = '60%仓位'
    elif avg_low < 160:
        res = '30%仓位'
    elif avg_low < 165:
        res = '正常交易'
    elif avg_low < 170:
        res = '减仓'
    else:
        res = '清仓'
    logger.info(res)
    return msg1, msg2, avg_low, res


def common_logic(df: pd.DataFrame):
    

    # 去掉未来1年到期的
    df['到期时间'] = pd.to_datetime(df['到期时间'])
    half_year = datetime.now() + timedelta(days=365)
    df = df[df['到期时间'] > half_year]

    # ST 有退市风险
    df = df[~df['正股名称'].str.contains(r'ST|\*')]

    # TODO: 不买银行的
    return df
    # df.sort_values(by=['现价', '转股价值', '转股溢价率'], ascending=[True, False, True])


def get_low_premium_rate_and_double_low(df: pd.DataFrame, num: int = 30):
    """
    低溢价率, 双低, 股性
    """
    df = common_logic(df)
    df = df[df['转股溢价率'] < 20]
    df = df.sort_values(by=['转股溢价率'], ascending=[True]).head(50)
    
    df = df[df['双低'] < 125]
    # df = df[df['现价'] < 110]
    df = df.sort_values(by=['双低'], ascending=[True]).head(num)

    return df


def get_double_low_and_low_premium_rate(df: pd.DataFrame, num: int = 30):
    """
    双低, 低溢价率, 债性
    """
    df = common_logic(df)
    
    df = df[df['双低'] < 125]
    df = df[df['现价'] < 110]
    df = df[df['转股溢价率'] < 20]
    df = df.sort_values(by=['双低'], ascending=[True]).head(50)
    
    df = df.sort_values(by=['转股溢价率'], ascending=[True]).head(num)

    return df


def get_logic_func(avg_low: float):
    if avg_low < 160:
        logic_func = get_low_premium_rate_and_double_low
    else:
        logic_func = get_double_low_and_low_premium_rate
    return logic_func


def get_unlisted_bonds(df: pd.DataFrame) -> list:
    """
    获取未上市债券
    """
    return df[df['上市日期'].isna()]['债券代码'].to_list()


def create_yield_curve_chart(df_rate: pd.DataFrame):
    """
    创建国债收益率曲线图
    """
    # 创建收益率曲线图
    fig = go.Figure()
    
    # 添加不同期限的收益率曲线
    fig.add_trace(go.Scatter(
        x=df_rate['日期'],
        y=df_rate['美国国债收益率10年'],
        mode='lines',
        name='美国国债收益率10年',
        line=dict(width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=df_rate['日期'],
        y=df_rate['中国国债收益率10年'],
        mode='lines',
        name='中国国债收益率10年',
        line=dict(width=3, color='red')  # 10年期用红色突出显示
    ))
    
    # 更新图表布局
    fig.update_layout(
        title='国债10年收益率曲线',
        xaxis_title='日期',
        yaxis_title='收益率 (%)',
        hovermode='x unified',
        height=600,
        showlegend=True,
        font=dict(size=12),
        margin=dict(l=50, r=50, t=80, b=50),
        plot_bgcolor='rgba(240, 240, 240, 0.5)',
        paper_bgcolor='rgba(255, 255, 255, 0.9)'
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
    
    return fig


dash.register_page(__name__)

# TODO: auto set file
path = Path('datas/raw/bonds/conv_20251022.csv')
# datas/raw/bonds/conv_20250903.csv
path_old = Path('datas/raw/bonds/conv_20250903.csv')
path_base_info = Path('datas/raw/bonds/ef_get_all_base_info.csv')
path_rate = Path('datas/raw/bonds/ak_cn_us_rate_20250925.csv')


df = pd.read_csv(str(path))
df_old = pd.read_csv(str(path_old))
df_base_info = pd.read_csv(str(path_base_info))
unlisted_bonds = get_unlisted_bonds(df_base_info)

# 加载国债收益率数据
df_rate = pd.read_csv(str(path_rate))
df_rate['日期'] = pd.to_datetime(df_rate['日期'])
# 按日期排序，确保时间序列正确
df_rate = df_rate.sort_values('日期')


msg1, msg2, avg_low, res = judge_bonds(df)
logic_func = get_logic_func(avg_low)

df = df[~df['代码'].isin(unlisted_bonds)]
df = logic_func(df)
df = df.sort_values(by=['转股价值'], ascending=[False])

df_old = df_old[~df_old['代码'].isin(unlisted_bonds)]
df_old = logic_func(df_old)
df_old = df_old.sort_values(by=['转股价值'], ascending=[False])


# breakpoint()

# 创建国债收益率曲线图
yield_curve_fig = create_yield_curve_chart(df_rate)

# 创建资产影响表格数据
asset_impact_data = [
    {
        '国债收益率变化': '📈 上升（利息高）',
        '股票': '↓',
        '房地产': '↓', 
        '债券': '↓',
        '黄金/比特币': '↓',
        '汇率（本币）': '↑'
    },
    {
        '国债收益率变化': '📉 下降（利息低）',
        '股票': '↑',
        '房地产': '↑',
        '债券': '↑',
        '黄金/比特币': '↑',
        '汇率（本币）': '↓'
    }
]


layout = dbc.Container(
    [
        # 国债分析部分
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader(
                                html.H4("📊 国债收益率分析", className="mb-0"),
                                className="bg-primary text-white"
                            ),
                            dbc.CardBody(
                                [
                                    html.H5("国债收益率变化对各类资产的影响", className="card-title"),
                                    dash_table.DataTable(
                                        data=asset_impact_data,
                                        style_table={
                                            'overflowX': 'auto', 
                                            'width': '100%',
                                            'borderRadius': '8px'
                                        },
                                        style_cell={
                                            'textAlign': 'center',
                                            'padding': '12px',
                                            'fontSize': 14,
                                            'fontFamily': 'Arial',
                                            'border': '1px solid #dee2e6'
                                        },
                                        style_header={
                                            'backgroundColor': '#007bff',
                                            'color': 'white',
                                            'fontWeight': 'bold',
                                            'textAlign': 'center'
                                        },
                                        style_data_conditional=[
                                            {
                                                'if': {'column_id': '国债收益率变化'},
                                                'fontWeight': 'bold',
                                                'backgroundColor': '#f8f9fa'
                                            }
                                        ]
                                    ),
                                    html.Hr(),
                                    dcc.Graph(figure=yield_curve_fig)
                                ]
                            )
                        ],
                        className="mb-4 shadow-sm"
                    ),
                    width=12
                )
            ]
        ),
        
        # 可转债分析部分
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader(
                                html.H4("💼 可转债投资分析", className="mb-0"),
                                className="bg-success text-white"
                            ),
                            dbc.CardBody(
                                [
                                    html.H4("国内可转债投资策略", className="card-title"),
                                    html.P("不买银行的", className="text-muted"),
                                    dbc.Alert(
                                        [
                                            html.H5("市场分析", className="alert-heading"),
                                            html.P(f"{msg1}", className="mb-1"),
                                            html.P(f"{msg2}", className="mb-1"),
                                            html.Hr(),
                                            html.H4(f"推荐操作：{res}", className="mb-0 text-danger")
                                        ],
                                        color="info",
                                        className="mb-3"
                                    ),
                                    
                                    # 筛选结果表格
                                    html.H5(f"{path.name}筛选结果", className="mt-4"),
                                    dash_table.DataTable(
                                        data=df.to_dict('records'),
                                        style_table={
                                            'overflowX': 'auto',
                                            'borderRadius': '8px'
                                        },
                                        style_cell={
                                            'padding': '8px',
                                            'fontSize': 12,
                                            'border': '1px solid #dee2e6'
                                        },
                                        style_header={
                                            'backgroundColor': '#28a745',
                                            'color': 'white',
                                            'fontWeight': 'bold'
                                        },
                                        sort_action='native',
                                        page_size=10
                                    ),
                                    
                                    html.H5(f"{path_old.name}筛选结果", className="mt-4"),
                                    dash_table.DataTable(
                                        data=df_old.to_dict('records'),
                                        style_table={
                                            'overflowX': 'auto',
                                            'borderRadius': '8px'
                                        },
                                        style_cell={
                                            'padding': '8px',
                                            'fontSize': 12,
                                            'border': '1px solid #dee2e6'
                                        },
                                        style_header={
                                            'backgroundColor': '#28a745',
                                            'color': 'white',
                                            'fontWeight': 'bold'
                                        },
                                        sort_action='native',
                                        page_size=10
                                    ),
                                    
                                    # 交易建议
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    html.H5("需要买入", className="mt-4 text-success"),
                                                    dash_table.DataTable(
                                                        data=df.merge(
                                                            df_old, on='代码', suffixes=('', '_old'), 
                                                            how='outer', indicator=True
                                                        ).query('_merge == "left_only"').drop('_merge', axis=1).to_dict('records'),
                                                        style_table={'overflowX': 'auto'},
                                                        style_cell={'padding': '6px', 'fontSize': 11},
                                                        style_header={'backgroundColor': '#28a745', 'color': 'white'},
                                                        sort_action='native'
                                                    )
                                                ],
                                                width=4
                                            ),
                                            dbc.Col(
                                                [
                                                    html.H5("需要卖出", className="mt-4 text-danger"),
                                                    dash_table.DataTable(
                                                        data=df.merge(
                                                            df_old, on='代码', suffixes=('', '_old'), 
                                                            how='outer', indicator=True
                                                        ).query('_merge == "right_only"').drop('_merge', axis=1).to_dict('records'),
                                                        style_table={'overflowX': 'auto'},
                                                        style_cell={'padding': '6px', 'fontSize': 11},
                                                        style_header={'backgroundColor': '#dc3545', 'color': 'white'},
                                                        sort_action='native'
                                                    )
                                                ],
                                                width=4
                                            ),
                                            dbc.Col(
                                                [
                                                    html.H5("继续持有", className="mt-4 text-primary"),
                                                    dash_table.DataTable(
                                                        data=df.merge(
                                                            df_old, on='代码', suffixes=('', '_old')
                                                        ).to_dict('records'),
                                                        style_table={'overflowX': 'auto'},
                                                        style_cell={'padding': '6px', 'fontSize': 11},
                                                        style_header={'backgroundColor': '#007bff', 'color': 'white'},
                                                        sort_action='native'
                                                    )
                                                ],
                                                width=4
                                            )
                                        ],
                                        className="mt-3"
                                    )
                                ]
                            )
                        ],
                        className="mb-4 shadow-sm"
                    ),
                    width=12
                )
            ]
        )
    ],
    fluid=True
)
