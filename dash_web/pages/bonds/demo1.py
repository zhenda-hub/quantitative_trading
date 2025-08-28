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

def judge_bonds(csv_file: str):
    df = pd.read_csv(csv_file)
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
    return msg1, msg2, res


def common_logic(csv_file: str):
    df = pd.read_csv(csv_file)

    # 去掉未来1年到期的
    df['到期时间'] = pd.to_datetime(df['到期时间'])
    half_year = datetime.now() + timedelta(days=365)
    df = df[df['到期时间'] > half_year]

    # ST 有退市风险
    df = df[~df['正股名称'].str.contains(r'ST|\*')]

    # TODO: 不买银行的
    return df
    # df.sort_values(by=['现价', '转股价值', '转股溢价率'], ascending=[True, False, True])


def double_common_logic(csv_file: str):
    df = common_logic(csv_file)
    df = df[df['双低'] < 125]
    return df


def get_double_low(csv_file: str, num: int = 30):
    """
    双低
    """
    df = double_common_logic(csv_file)
    df = df.sort_values(by=['双低'], ascending=[True]).head(num)
    return df


def get_double_low_and_low_premium_rate(csv_file: str, num: int = 30):
    """
    双低, 低溢价率
    """
    df = double_common_logic(csv_file)
    df = df.sort_values(by=['转股溢价率'], ascending=[True]).head(num)
    return df


def get_low_premium_rate_and_double_low(csv_file: str, num: int = 30):
    """
    低溢价率, 双低
    """
    df = common_logic(csv_file)
    df = df.sort_values(by=['转股溢价率'], ascending=[True]).head(40)
    df = df.sort_values(by=['双低'], ascending=[True]).head(num)

    return df


def get_final_list(csv_file: str):
    """
    最终名单
    """
    df1 = get_double_low(csv_file)
    df2 = get_double_low_and_low_premium_rate(csv_file)
    df3 = get_low_premium_rate_and_double_low(csv_file)
    final_df = df1.merge(df2).merge(df3)  # 全合并

    final_df = final_df.sort_values(by=['转股价值'], ascending=[False])
    return final_df


dash.register_page(__name__)

path = Path('datas/raw/bonds/conv_20231223.csv')
path_old = Path('datas/raw/bonds/conv_20231220.csv')

msg1, msg2, res = judge_bonds(str(path))
df = get_final_list(str(path))
df_old = get_final_list(str(path_old))
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
                        html.H5(f"推荐操作：{res}"),
                        html.H6(f"{path.name}结果："),
                        dash_table.DataTable(
                            data=df.to_dict('records'),
                            style_table={'overflowX': 'auto'},
                            sort_action='native',
                        ),
                        html.H6(f"{path_old.name}结果："),
                        dash_table.DataTable(
                            data=df_old.to_dict('records'),
                            style_table={'overflowX': 'auto'},
                            sort_action='native',
                        ),
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
