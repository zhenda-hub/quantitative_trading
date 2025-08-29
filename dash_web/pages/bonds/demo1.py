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


dash.register_page(__name__)

# TODO: auto set file
path = Path('datas/raw/bonds/conv_20250829.csv')
path_old = Path('datas/raw/bonds/conv_20250825.csv')


df = pd.read_csv(str(path))
df_old = pd.read_csv(str(path_old))

msg1, msg2, avg_low, res = judge_bonds(df)
logic_func = get_logic_func(avg_low)

df = logic_func(df)
df = df.sort_values(by=['转股价值'], ascending=[False])
df_old = logic_func(df_old)
df_old = df_old.sort_values(by=['转股价值'], ascending=[False])


# breakpoint()


layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(html.Div(""), width=1),
                dbc.Col(html.Div(
                    children=[
                        html.H4("国内可转债， 不买银行的"),
                        html.H5(f"{msg1}"),
                        html.H5(f"{msg2}"),
                        html.H5(f"推荐操作：{res}!!!!!!!!!!!!!"),
                        html.Hr(),
                        html.H6(f"{path.name}筛选结果："),
                        dash_table.DataTable(
                            data=df.to_dict('records'),
                            style_table={'overflowX': 'auto'},
                            sort_action='native',
                        ),
                        html.H6(f"{path_old.name}筛选结果："),
                        dash_table.DataTable(
                            data=df_old.to_dict('records'),
                            style_table={'overflowX': 'auto'},
                            sort_action='native',
                        ),
                        html.Hr(),
                        html.H6("需要买入："),
                        dash_table.DataTable(
                            data=df.merge(df_old, on='代码', suffixes=('', '_old'), how='outer', indicator=True).query('_merge == "left_only"').drop('_merge', axis=1).to_dict('records'),
                            style_table={'overflowX': 'auto'},
                            sort_action='native',
                        ),
                        html.H6("需要卖出："),
                        dash_table.DataTable(
                            data=df.merge(df_old, on='代码', suffixes=('', '_old'), how='outer', indicator=True).query('_merge == "right_only"').drop('_merge', axis=1).to_dict('records'),
                            style_table={'overflowX': 'auto'},
                            sort_action='native',
                        ),
                        html.H6("继续持有："),
                        dash_table.DataTable(
                            data=df.merge(df_old, on='代码', suffixes=('', '_old')).to_dict('records'),
                            style_table={'overflowX': 'auto'},
                            sort_action='native',
                        ),
                    ]
                ), width=10),
                dbc.Col(html.Div(""), width=1),
            ]
        )
    ]
)
