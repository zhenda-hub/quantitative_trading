"""行业轮动页

表1「行业轮动榜」：datas/processed/n_indexes/industry_rotation.csv
    - 动量（20/60/120 日）+ 相对强弱（RS vs 沪深300）+ 当日热度 + 估值分位 + 可买 ETF
    - 支持滑块筛选：动量分位下限、PE 分位上限，可选是否包含无 PE 分位的行业
表2「行业估值分位」：国证口径全量（折叠收起，需要交叉验证时展开）

口径说明：
- 动量分位、RS：有完整历史（496 板块 × 近 3 年日线）
- PE 分位：国证静态 PE（829 个交易日历史），名称匹配到东财板块，覆盖约 29%
- 动态 PE：当日快照，只能横向比较，无历史算不出分位
"""
from pathlib import Path

import pandas as pd
from dash import Input, Output, callback, dash_table, dcc, html
import dash
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/rotation")

ROTATION_CSV = Path("datas/processed/n_indexes/industry_rotation.csv")
PE_CSV = Path("datas/processed/n_indexes/industry_pe_cninfo.csv")
PICKS_CSV = Path("datas/processed/n_indexes/industry_rotation_picks.csv")

COLD, HOT = 20.0, 80.0
TRADING_DAYS_1Y = 244

# 默认筛选阈值（与脚本 picks 一致）
DEFAULT_MOMENTUM = 80
DEFAULT_PE = 20


def num(column_id, name, spec=".2f"):
    return {"id": column_id, "name": name, "type": "numeric", "format": {"specifier": spec}}


def load_rotation() -> tuple[pd.DataFrame, str]:
    if not ROTATION_CSV.exists():
        return pd.DataFrame(), "无数据"
    df = pd.read_csv(ROTATION_CSV, dtype={"板块代码": str})
    kline_date = str(df["K线日期"].mode().iloc[0]) if "K线日期" in df else "未知"
    return df, kline_date


def load_pe_percentile() -> tuple[pd.DataFrame, str]:
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
        window_1y = series[-TRADING_DAYS_1Y:]
        rows.append({
            "行业": name,
            "层级": int(level),
            "最新PE": round(float(series[-1]), 2),
            "近3年分位": round(float((series <= series[-1]).mean() * 100), 1),
            "近1年分位": round(float((window_1y <= series[-1]).mean() * 100), 1),
            "样本期数": len(series),
        })
    result = pd.DataFrame(rows)
    result["分档"] = pd.cut(
        result["近3年分位"], bins=[-1, COLD, HOT, 101], labels=["偏冷", "中性", "偏热"]
    ).astype(str)
    return result.sort_values("近3年分位"), latest_day


def picks_count() -> int:
    if not PICKS_CSV.exists():
        return 0
    try:
        return len(pd.read_csv(PICKS_CSV, dtype={"板块代码": str}))
    except Exception:  # noqa: BLE001
        return 0


rotation, kline_date = load_rotation()
pe_table, pe_date = load_pe_percentile()
script_picks = picks_count()

rotation_columns = [
    {"id": "序号", "name": "#", "type": "numeric"},
    {"id": "板块", "name": "板块"},
    num("动量分位", "动量分位", ".1f"),
    num("20日涨幅", "20日 %"),
    num("60日涨幅", "60日 %"),
    num("120日涨幅", "120日 %"),
    num("RS20", "RS20 (超额)"),
    num("今日涨幅", "今日 %"),
    num("换手率", "换手 %"),
    num("成交额(亿)", "成交额(亿)", ",.1f"),
    num("动态PE", "动态PE", ".1f"),
    num("PE分位", "PE分位 %", ".1f"),
    {"id": "ETF名称", "name": "可买 ETF"},
    num("ETF成交额(亿)", "ETF成交额(亿)", ",.2f"),
]

pe_columns = [
    {"id": "行业", "name": "行业"},
    {"id": "层级", "name": "层级", "type": "numeric"},
    num("最新PE", "最新PE"),
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
                "动量定强弱 + 估值定贵贱 + ETF 落地。拖下面的滑块筛候选池。",
                className="text-center text-muted mb-4",
            ),
        ])
    ]),

    # 筛选控件
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("动量分位 ≥", className="fw-bold small mb-1"),
                            dcc.Slider(
                                id="momentum-min",
                                min=0, max=100, step=5, value=DEFAULT_MOMENTUM,
                                marks={0: "0", 50: "50", 80: "80", 100: "100"},
                                tooltip={"placement": "bottom"},
                            ),
                            html.Small(
                                "越高越强。80 = 只要最强的 20% 板块（按 20/60/120 日涨幅加权排名）；"
                                "拉到 0 = 不限强弱。",
                                className="text-muted d-block mt-4",
                            ),
                        ], md=6),
                        dbc.Col([
                            html.Label("PE 分位 ≤（国证静态 PE）", className="fw-bold small mb-1"),
                            dcc.Slider(
                                id="pe-max",
                                min=0, max=100, step=5, value=DEFAULT_PE,
                                marks={0: "0", 20: "20", 50: "50", 100: "100"},
                                tooltip={"placement": "bottom"},
                            ),
                            html.Small(
                                "越低越便宜。20 = 只要历史上最便宜的 20%；100 = 不限估值。"
                                "仅 145/496 个板块有分位（东财板块名与国证行业名对不上）。",
                                className="text-muted d-block mt-4",
                            ),
                        ], md=6),
                    ], className="mb-2"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Checklist(
                                id="include-no-pe",
                                options=[{"label": " 包含「无 PE 分位」的行业（约 351 个，名称未匹配上）",
                                          "value": "yes"}],
                                value=[],
                                switch=True,
                                className="small",
                            ),
                            html.Small(
                                "不勾：只在有估值的板块里筛（默认 5 个）；勾上：这 351 个不受 PE 条件限制，命中会大幅增加（同条件下 53 个）。",
                                className="text-muted d-block",
                            ),
                        ], md=8),
                        dbc.Col([
                            html.Div(id="pick-count", className="text-end fw-bold small"),
                        ], md=4),
                    ]),
                ])
            ], className="border-0 shadow-sm")
        ], width=12)
    ], className="mb-3"),

    # 表1
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.Div([
                        html.H5("① 行业轮动榜", className="mb-0"),
                        html.Small(
                            f"{len(rotation)} 个东财板块 · K线至 {kline_date} · "
                            f"脚本候选池（默认阈值）{script_picks} 个 · 点击表头排序",
                            className="text-muted",
                        ),
                    ], className="d-flex align-items-center gap-3 flex-wrap"),
                ]),
                dbc.CardBody([
                    html.P(
                        "动量分位 = 20/60/120 日涨幅百分位加权（0.5/0.3/0.2）；"
                        "RS20 = 20 日涨幅 − 沪深300 同期（pp）。"
                        "PE 分位用国证静态 PE（有 829 天历史），动态 PE 仅当日值、无历史分位。"
                        "周期行业（煤炭/钢铁/有色/化工/航运/养殖）PE 分位易失真。",
                        className="text-muted small",
                    ),
                    dash_table.DataTable(
                        id="rotation-table",
                        columns=rotation_columns,
                        data=[],
                        sort_action="native",
                        sort_by=[{"column_id": "动量分位", "direction": "desc"}],
                        page_action="native",
                        page_size=20,
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

    # 表2（折叠）
    dbc.Row([
        dbc.Col([
            dbc.Accordion([
                dbc.AccordionItem([
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
                ], title=f"② 行业估值分位（国证口径，{len(pe_table)} 个行业 · 数据日 {pe_date}）"),
            ], start_collapsed=True, flush=True),
        ], width=12)
    ]),

], fluid=True, className="py-4", style={"backgroundColor": "#f8f9fa"})


@callback(
    Output("rotation-table", "data"),
    Output("pick-count", "children"),
    Input("momentum-min", "value"),
    Input("pe-max", "value"),
    Input("include-no-pe", "value"),
)
def apply_filter(momentum_min, pe_max, include_no_pe):
    """按动量下限 + PE 分位上限筛选轮动榜"""
    if rotation.empty:
        return [], "无数据"

    momentum_min = DEFAULT_MOMENTUM if momentum_min is None else momentum_min
    pe_max = DEFAULT_PE if pe_max is None else pe_max
    has_pe = rotation["PE分位"].notna()

    mask = rotation["动量分位"] >= momentum_min
    if "yes" in (include_no_pe or []):
        mask &= (~has_pe) | (rotation["PE分位"] <= pe_max)
    else:
        mask &= has_pe & (rotation["PE分位"] <= pe_max)

    picked = rotation[mask].copy()
    picked = picked.sort_values("动量分位", ascending=False)
    picked.insert(0, "序号", range(1, len(picked) + 1))

    with_etf = int(picked["ETF名称"].notna().sum()) if "ETF名称" in picked else 0
    label = (
        f"命中 {len(picked)} 个板块 · 其中 {with_etf} 个有 ETF 可买"
        if len(picked)
        else "无命中：放宽动量或 PE 阈值试试"
    )
    return picked.to_dict("records"), label
