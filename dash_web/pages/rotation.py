"""行业轮动页

表1「行业轮动榜」：datas/processed/n_indexes/industry_rotation.csv
    动量（20/60/120 日）+ 相对强弱（RS vs 沪深300）+ 当日热度 + 估值分位 + 可买 ETF
表2「行业估值分位」：datas/processed/n_indexes/industry_pe_cninfo.csv
    国证 293 行业的静态 PE 在近 3 年 / 近 1 年历史中的位置

两张表来自不同口径（东财板块 / 国证行业），并列展示，不做硬合并。
"""
from pathlib import Path

import pandas as pd
from dash import dash_table, html
import dash
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/rotation")

ROTATION_CSV = Path("datas/processed/n_indexes/industry_rotation.csv")
PE_CSV = Path("datas/processed/n_indexes/industry_pe_cninfo.csv")

COLD, HOT = 20.0, 80.0
TRADING_DAYS_1Y = 244


def num(column_id, name, spec=".2f", sortable=True):
    return {"id": column_id, "name": name, "type": "numeric", "format": {"specifier": spec}}


def load_rotation() -> tuple[pd.DataFrame, str, str]:
    """行业轮动榜（动量 + RS + 热度 + 估值 + ETF）"""
    if not ROTATION_CSV.exists():
        return pd.DataFrame(), "无数据", "无数据"
    df = pd.read_csv(ROTATION_CSV, dtype={"板块代码": str})
    kline_date = str(df["K线日期"].mode().iloc[0]) if "K线日期" in df else "未知"
    return df, kline_date, ""


def load_pe_percentile() -> tuple[pd.DataFrame, str]:
    """国证行业 PE 分位（近 3 年 / 近 1 年）"""
    if not PE_CSV.exists():
        return pd.DataFrame(), "无数据"

    df = pd.read_csv(PE_CSV, dtype={"行业编码": str})
    df["静态市盈率-加权平均"] = pd.to_numeric(df["静态市盈率-加权平均"], errors="coerce")
    df = df.dropna(subset=["静态市盈率-加权平均"])
    df = df[df["静态市盈率-加权平均"] > 0]

    latest_day = df["日期"].max()
    rows = []
    for (code, level, name), group in df.groupby(["行业编码", "行业层级", "行业名称"]):
        series = group.sort_values("日期")["静态市盈率-加权平均"].values
        if len(series) < 60:
            continue
        current = series[-1]
        window_1y = series[-TRADING_DAYS_1Y:]
        rows.append({
            "行业": name,
            "层级": int(level),
            "最新PE": round(float(current), 2),
            "近3年分位": round(float((series <= current).mean() * 100), 1),
            "近1年分位": round(float((window_1y <= current).mean() * 100), 1),
            "样本期数": len(series),
        })

    result = pd.DataFrame(rows)
    result["分档"] = pd.cut(
        result["近3年分位"], bins=[-1, COLD, HOT, 101], labels=["偏冷", "中性", "偏热"]
    ).astype(str)
    return result.sort_values("近3年分位"), latest_day


rotation, kline_date, _ = load_rotation()
pe_table, pe_date = load_pe_percentile()

rotation_columns = [
    {"id": "排名", "name": "排名", "type": "numeric"},
    {"id": "板块", "name": "板块"},
    num("动量分位", "动量分位", ".1f"),
    num("20日涨幅", "20日 %", ".2f"),
    num("60日涨幅", "60日 %", ".2f"),
    num("120日涨幅", "120日 %", ".2f"),
    num("RS20", "RS20 (超额)", ".2f"),
    num("今日涨幅", "今日 %", ".2f"),
    num("换手率", "换手 %", ".2f"),
    num("成交额(亿)", "成交额(亿)", ",.1f"),
    num("动态PE", "动态PE", ".1f"),
    num("PE分位", "PE分位 %", ".1f"),
    {"id": "ETF名称", "name": "可买 ETF"},
    num("ETF成交额(亿)", "ETF成交额(亿)", ",.2f"),
]

pe_columns = [
    {"id": "行业", "name": "行业"},
    {"id": "层级", "name": "层级", "type": "numeric"},
    num("最新PE", "最新PE", ".2f"),
    num("近3年分位", "近3年分位 %", ".1f"),
    num("近1年分位", "近1年分位 %", ".1f"),
    {"id": "分档", "name": "分档"},
    {"id": "样本期数", "name": "样本期数", "type": "numeric"},
]

layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H3("行业轮动", className="text-center mt-4 mb-1"),
            html.P(
                "表1：动量定强弱（买强的还是买弱的，自己判断）+ 估值定贵贱 + ETF 落地。"
                "表2：国证口径的 PE 历史分位，供交叉验证。",
                className="text-center text-muted mb-4",
            ),
        ])
    ]),

    # 表1：行业轮动榜
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.Div([
                        html.H5("① 行业轮动榜", className="mb-0"),
                        html.Small(
                            f"{len(rotation)} 个东财板块 · K线至 {kline_date} · 点击表头排序",
                            className="text-muted",
                        ),
                    ], className="d-flex align-items-center gap-3 flex-wrap"),
                ]),
                dbc.CardBody([
                    html.P(
                        "动量分位 = 20/60/120 日涨幅百分位的加权（0.5/0.3/0.2，0-100，越高越强）；"
                        "RS20 = 20 日涨幅减沪深300 同期涨幅（pp）。PE 分位来自国证口径（名称匹配，"
                        "未匹配留空），周期行业（煤炭/钢铁/有色/化工/航运/养殖）PE 分位易失真。",
                        className="text-muted small",
                    ),
                    dash_table.DataTable(
                        id="rotation-table",
                        columns=rotation_columns,
                        data=rotation.to_dict("records"),
                        sort_action="native",
                        sort_by=[{"column_id": "动量分位", "direction": "desc"}],
                        page_action="native",
                        page_size=25,
                        style_table={"overflowX": "auto"},
                        style_cell={"fontSize": 12, "padding": "4px 8px", "textAlign": "right"},
                        style_cell_conditional=[
                            {"if": {"column_id": "板块"}, "textAlign": "left", "minWidth": "120px"},
                            {"if": {"column_id": "ETF名称"}, "textAlign": "left", "minWidth": "160px"},
                        ],
                        style_header={"fontWeight": "bold", "backgroundColor": "#f1f3f5"},
                        style_data_conditional=[
                            {"if": {"filter_query": "{今日涨幅} > 0", "column_id": "今日涨幅"}, "color": "#c92a2a"},
                            {"if": {"filter_query": "{今日涨幅} < 0", "column_id": "今日涨幅"}, "color": "#2b8a3e"},
                            {"if": {"filter_query": "{RS20} > 0", "column_id": "RS20"}, "color": "#c92a2a"},
                            {"if": {"filter_query": "{RS20} < 0", "column_id": "RS20"}, "color": "#2b8a3e"},
                            {"if": {"filter_query": "{PE分位} < 20", "column_id": "PE分位"}, "color": "#2b8a3e"},
                            {"if": {"filter_query": "{PE分位} > 80", "column_id": "PE分位"}, "color": "#c92a2a"},
                        ],
                    )
                ]),
            ], className="border-0 shadow-sm")
        ], width=12)
    ], className="mb-4"),

    # 表2：行业估值分位
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.Div([
                        html.H5("② 行业估值分位（国证口径）", className="mb-0"),
                        html.Small(
                            f"{len(pe_table)} 个行业 · 数据日 {pe_date} · "
                            f"<{COLD:.0f}% 偏冷 / >{HOT:.0f}% 偏热",
                            className="text-muted",
                        ),
                    ], className="d-flex align-items-center gap-3 flex-wrap"),
                ]),
                dbc.CardBody([
                    dash_table.DataTable(
                        id="pe-table",
                        columns=pe_columns,
                        data=pe_table.to_dict("records"),
                        sort_action="native",
                        sort_by=[{"column_id": "近3年分位", "direction": "asc"}],
                        page_action="native",
                        page_size=20,
                        style_table={"overflowX": "auto"},
                        style_cell={"fontSize": 12, "padding": "4px 8px", "textAlign": "right"},
                        style_cell_conditional=[
                            {"if": {"column_id": "行业"}, "textAlign": "left", "minWidth": "140px"},
                        ],
                        style_header={"fontWeight": "bold", "backgroundColor": "#f1f3f5"},
                        style_data_conditional=[
                            {"if": {"filter_query": "{分档} = 偏冷"}, "color": "#2b8a3e"},
                            {"if": {"filter_query": "{分档} = 偏热"}, "color": "#c92a2a"},
                            {"if": {"filter_query": "{层级} = 4"}, "color": "#adb5bd"},
                        ],
                    )
                ]),
            ], className="border-0 shadow-sm")
        ], width=12)
    ]),

], fluid=True, className="py-4", style={"backgroundColor": "#f8f9fa"})
