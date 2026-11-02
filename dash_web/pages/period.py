from pathlib import Path
from datetime import datetime

from dash import Dash, dcc, html, Input, Output, callback, dash_table
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import dash
from loguru import logger

from utils.clean_data import merge_res
from utils.chart_utils import CHART_HEIGHT

# import sys
#
# # Build paths inside the project like this: BASE_DIR / 'subdir'.
# BASE_DIR = Path(__file__).resolve().parent.parent
# sys.path.append(str(BASE_DIR))

dash.register_page(__name__)
# app = Dash(__name__, use_pages=True, pages_folder="my_apps")



# UNEMP_NAME_FILE_DICT = {
#     'australia': "australia_unemps.csv",
#     'canada': "canada_unemps.csv",
#     'china': "china_unemps.csv",
#     'euro': "euro_unemps.csv",
#     'japan': "japan_unemps.csv",
#     'usa': "usa_unemps.csv",
# }


def needs_rebuild(output_path: Path, raw_paths: list) -> bool:
    """输出不存在, 或任一源文件比输出新 -> 需要重建"""
    if not output_path.exists():
        return True
    output_mtime = output_path.stat().st_mtime
    newer = [p.name for p in raw_paths if p.exists() and p.stat().st_mtime > output_mtime]
    if newer:
        logger.info(f'{output_path.name} 已过期, 源文件更新: {newer}')
        return True
    return False


def merge_gdps(res_path: str):
    """
    GDP
    """

    base_path = Path('datas/raw/gdps')
    GDP_NAME_FILE_DICT = {
        'china': "ak_china_gdp.csv",
        'euro': "ak_euro_gdp.csv",
        'usa': "ak_usa_gdp.csv",
    }
    csv_paths = [base_path / v for v in GDP_NAME_FILE_DICT.values()]

    final_gdp_path = Path(res_path)
    if not needs_rebuild(final_gdp_path, csv_paths):
        logger.info('gdps 已是最新')
        return

    new_columns = list(GDP_NAME_FILE_DICT.keys())
    new_columns.insert(0, 'date')

    target_columns = ['日期', '今值']
    addr = merge_res(csv_paths, target_columns, new_columns, final_gdp_path)
    logger.info('addr:', addr)


def merge_cpis(res_path: str):
    """
    消费者物价指数年率
    """
    base_path = Path('datas/raw/cpis')

    CPI_NAME_FILE_DICT = {
        'china': "macro_china_cpi_yearly.csv",
        'euro': "macro_euro_cpi_yoy.csv",
        'australia': "macro_australia_cpi_yearly.csv",
        'canada': "macro_canada_cpi_yearly.csv",
        'japan': "macro_japan_cpi_yearly.csv",
        'usa': "macro_usa_cpi_yoy.csv",
    }

    csv_paths = [base_path / v for v in CPI_NAME_FILE_DICT.values()]

    final_cpi_path = Path(res_path)
    if not needs_rebuild(final_cpi_path, csv_paths):
        logger.info('cpis 已是最新')
        return

    new_columns = list(CPI_NAME_FILE_DICT.keys())
    new_columns.insert(0, 'date')

    target_columns = ['时间', '现值']
    # 部分源(中国/欧元)表头是 '日期/今值', 需归一后才能合并
    column_aliases = {
        '时间': ['时间', '日期'],
        '现值': ['现值', '今值'],
    }
    addr = merge_res(
        csv_paths,
        target_columns,
        new_columns,
        final_cpi_path,
        column_aliases=column_aliases,
    )
    logger.info('addr:', addr)


# def merge_unemps():
#     """
#     失业率
#     """
#     base_path = Path('datas/unemps')
#     csv_paths = [base_path / v for v in UNEMP_NAME_FILE_DICT.values()]

#     new_columns = list(UNEMP_NAME_FILE_DICT.keys())
#     new_columns.insert(0, 'date')

#     target_columns = ['时间', '现值']
#     # breakpoint()
#     addr = merge_res(csv_paths, target_columns, new_columns, f'datas/processed/unemps/all_unemps_data_{date_str}.csv')
#     print('addr:', addr)
    
    
def gene_fig(csv_path: str, yaxis_title: str, title: str):
    df = pd.read_csv(csv_path)
    # breakpoint()
    # fig = px.line(
    fig = px.scatter(
        df,
        x="date",
        y=df.columns,
        hover_data={"date": "|%B %d, %Y"},
        title=title,

    )
    fig.update_layout(
        height=CHART_HEIGHT,
        # xaxis_title='花萼宽度（cm）',
        yaxis_title=yaxis_title,

    )
    # print('fig.layout.height', fig.layout.height)
    # print('fig.layout.width', fig.layout.width)

    fig.update_xaxes(
        # dtick="M1",
        # tickformat="%b\n%Y",
        # tickformat="%Y",
        rangeslider_visible=True,  # 添加滑动块
        # 范围选择器按钮
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1month", step="month", stepmode="backward"),
                dict(count=6, label="6month", step="month", stepmode="backward"),  # TODO: set default
                # dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1year", step="year", stepmode="backward"),
                dict(count=3, label="3year", step="year", stepmode="backward"),
                dict(count=5, label="5year", step="year", stepmode="backward"),
                dict(count=10, label="10year", step="year", stepmode="backward"),
                dict(count=20, label="20year", step="year", stepmode="backward"),
                dict(step="all")
            ])
        )
        # ticklabelmode="period"
    )

    return fig


def _last_period(csv_path) -> str:
    """取 csv 里最后一个「真正有数据」的日期, 用于标题标注数据截止期

    注意: 跳过所有数值列均为 NaN 的行（未来发布日会造成虚假的最新期）。
    """
    try:
        df = pd.read_csv(csv_path)
        value_cols = [c for c in df.columns if c != 'date']
        if value_cols:
            df = df.dropna(subset=value_cols, how='all')
        last = pd.to_datetime(df['date'], errors='coerce').max()
        return last.strftime('%Y-%m') if pd.notna(last) else '未知'
    except Exception as error:  # noqa: BLE001
        logger.warning(f'读取 {csv_path} 失败: {error}')
        return '未知'


gdp_res = 'datas/processed/gdps/all_data.csv'
cpi_res = 'datas/processed/cpis/all_data.csv'
std_gdp_res = 'datas/processed/gdps/std_gdp_growth.csv'
merge_gdps(gdp_res)
merge_cpis(cpi_res)

# 标准口径 GDP（FRED + 国家统计局）: 文件缺失时尝试现抓一次
if not Path(std_gdp_res).exists():
    logger.warning(f'{std_gdp_res} 不存在, 尝试重新抓取')
    try:
        from utils.gdp_std import build_std_gdp

        build_std_gdp()
    except Exception as error:  # noqa: BLE001
        logger.error(f'标准口径 GDP 抓取失败: {error}')

if Path(std_gdp_res).exists():
    fig_gdp = gene_fig(
        std_gdp_res,
        '实际GDP同比 (%)',
        f"实际GDP同比（季调 SNA2008；中国为累计同比） 数据截至 {_last_period(std_gdp_res)}",
    )
else:
    fig_gdp = go.Figure()
    fig_gdp.update_layout(
        height=CHART_HEIGHT,
        title='标准口径 GDP 数据缺失，请运行: python -m utils.gdp_std',
    )

fig_cpi = gene_fig(
    cpi_res,
    'CPI年率 (%)',
    f"CPI年率 数据截至 {_last_period(cpi_res)}"
    "（e.g., 数值为2.5，意味着物价一年涨2.5%）",
)
# fig_unemp = gene_fig("datas/processed/unemps/all_unemps_data.csv", '失业率', '失业率')


layout = html.Div(
    [
        html.H4("全球经济周期"),
        html.H6("GDP同比，经济发展状况"),
        html.P(
            "美国 / 德国 / 欧元区19 为 FRED 实际GDP（季调、链式、SNA2008）自算同比；"
            "中国为国家统计局季度累计同比 —— 口径与其他三条不同，看趋势为主。"
        ),
        html.H6("CPI年率，反应物价波动状况"),
        # html.H6("失业率， 经济周期中，通常和GDP，CPI成反方向"),
        html.H6("GDP， CPI表示经济周期：上升，高点，下降，低点"),
        html.H5("经济周期阶段特征"),
        dbc.Table(
            [
                html.Thead(
                    html.Tr([
                        html.Th("经济周期阶段"),
                        html.Th("GDP变化趋势"),
                        html.Th("CPI变化趋势")
                    ])
                ),
                html.Tbody([
                    html.Tr([
                        html.Td("复苏期"),
                        html.Td("上升 ↑"),
                        html.Td("下降 ↓")
                    ]),
                    html.Tr([
                        html.Td("过热期"),
                        html.Td("上升 ↑"),
                        html.Td("上升 ↑")
                    ]),
                    html.Tr([
                        html.Td("滞胀期"),
                        html.Td("下降 ↓"),
                        html.Td("上升 ↑")
                    ]),
                    html.Tr([
                        html.Td("衰退期"),
                        html.Td("下降 ↓"),
                        html.Td("下降 ↓")
                    ])
                ])
            ],
            bordered=True,
            striped=True,
            hover=True,
            responsive=True,
            style={
                'margin-top': '20px',
                'margin-bottom': '20px'
            }
        ),
        # dcc.Checklist(
        #     id="toggle-rangeslider",
        #     options=[{"label": "Include Rangeslider", "value": "slider"}],
        #     value=["slider"],
        # ),
        # dcc.Graph(id="graph3"),


        dcc.Graph(figure=fig_gdp,),
        dcc.Graph(figure=fig_cpi,),
        # dcc.Graph(figure=fig_unemp,),
    ]
)


# @callback(
#     Output("graph3", "figure"),
#     Input("toggle-rangeslider", "value"),
# )
# def display_candlestick2(value):
#     # "https://raw.githubusercontent.com/plotly/datasets/master/finance-charts-apple.csv"
#     df = pd.read_csv("datas/indexes/all_indexes_data.csv")
#
#     fig = px.line(df, x="date", y=df.columns,
#                   hover_data={"date": "|%B %d, %Y"},
#                   title='custom tick labels with ticklabelmode="period"')
#     fig.update_xaxes(
#         dtick="M1",
#         tickformat="%b\n%Y",
#         ticklabelmode="period")
#     fig.update_layout(xaxis_rangeslider_visible="slider" in value)
#     return fig


# # if __name__ == "__main__":
# #     app.run_server(debug=True)
