from datetime import datetime
from pathlib import Path

from dash import dcc, html
import plotly.graph_objects as go
import pandas as pd
import dash
import dash_bootstrap_components as dbc

dash.register_page(__name__, path='/', folder='')

NEWS_DIR = Path("datas/raw/news")

# 新闻源配置：path -> (列映射, 显示名, badge 颜色)
# 各源表头不同，统一成 title / summary / time / link / source 五列
NEWS_SOURCES = [
    {
        "path": NEWS_DIR / "ak_stock_info_global_em.csv",
        "columns": {"title": "标题", "summary": "摘要", "time": "发布时间", "link": "链接"},
        "name": "东财快讯",
        "badge": "primary",
    },
    {
        "path": NEWS_DIR / "ak_stock_info_global_ths.csv",
        "columns": {"title": "标题", "summary": "内容", "time": "发布时间", "link": "链接"},
        "name": "同花顺",
        "badge": "success",
    },
    {
        "path": NEWS_DIR / "ak_stock_info_cjzc_em.csv",
        "columns": {"title": "标题", "summary": "摘要", "time": "发布时间", "link": "链接"},
        "name": "财经早餐",
        "badge": "warning",
    },
    {
        # 新浪只有 时间 + 内容，没有标题和链接
        "path": NEWS_DIR / "ak_stock_info_global_sina.csv",
        "columns": {"summary": "内容", "time": "时间"},
        "name": "新浪",
        "badge": "info",
    },
    {
        # 财联社的日期和时间分两列
        "path": NEWS_DIR / "ak_stock_info_global_cls.csv",
        "columns": {"title": "标题", "summary": "内容"},
        "date_columns": ("发布日期", "发布时间"),
        "name": "财联社",
        "badge": "danger",
    },
]

NEWS_LIMIT = 150           # 页面展示的最大新闻条数
PER_SOURCE_LIMIT = 60      # 单一来源最多保留条数（否则高频快讯会把早餐/要闻挤没）
SUMMARY_MAX_CHARS = 120
TODAY_ONLY = False         # 只显示当日新闻（关：改用滚动时间窗）
NEWS_WINDOW_HOURS = 72     # 只显示最近 72 小时内的新闻


def _normalize_source(config: dict) -> pd.DataFrame:
    """把单个新闻源读成 title / summary / time / link / source / badge 六列"""
    path = config["path"]
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)
    df = df.rename(columns={v: k for k, v in config["columns"].items()})

    # 时间：普通源一列，财联社要拼 发布日期 + 发布时间
    if "date_columns" in config:
        date_col, time_col = config["date_columns"]
        if date_col in df.columns and time_col in df.columns:
            df["time"] = (
                df[date_col].astype(str).str.strip()
                + " "
                + df[time_col].astype(str).str.strip()
            )

    for column in ("title", "summary", "time", "link"):
        if column not in df.columns:
            df[column] = ""

    df = df[["title", "summary", "time", "link"]]
    df["title"] = df["title"].fillna("").astype(str).str.strip()
    df["summary"] = df["summary"].fillna("").astype(str).str.strip()

    # 没有标题的源（新浪）：用内容首句当标题
    blank = df["title"] == ""
    if blank.any():
        df.loc[blank, "title"] = (
            df.loc[blank, "summary"].str.split("。").str[0].str[:60]
        )

    # 摘要开头与标题重复时去掉那一段（新浪的【标题】、同花顺/东财的“标乄 + 细节”）
    def _strip_dup(summary: str, title: str) -> str:
        text = summary
        if not title or not text:
            return text
        for prefix in (f"【{title}】", title):
            if text.startswith(prefix):
                text = text[len(prefix):]
                break
        return text.lstrip("】】　 ，。:：")

    df["summary"] = [
        _strip_dup(summary, title)
        for summary, title in zip(df["summary"], df["title"])
    ]

    df["time"] = pd.to_datetime(df["time"], errors="coerce")
    df = df.dropna(subset=["time"])
    df = df[df["title"] != ""]

    df["source"] = config["name"]
    df["badge"] = config["badge"]
    return df


def load_news(limit: int = NEWS_LIMIT, per_source: int = PER_SOURCE_LIMIT):
    """合并全部新闻源，只取当日新闻，按时间倒序返回

    实测可用量：东财快讯 200 / 同花顺 20 / 新浪 20 / 财联社 20 / 财经早餐 400

    处理顺序：合并 → 去重 → **只留当日** → 每源配额粗筛 → 全局按时间排序取 limit。
    每源配额是为了避免高频快讯把每天只有 1 条的财经早餐挤掉。

    Returns:
        (DataFrame, 日期说明文字)；当日无新闻时退栈到最新一天并标注。
    """
    empty = pd.DataFrame(columns=["title", "summary", "time", "link", "source", "badge"])

    frames = [_normalize_source(config) for config in NEWS_SOURCES]
    frames = [frame for frame in frames if not frame.empty]
    if not frames:
        return empty, "无数据"

    df = pd.concat(frames, ignore_index=True)
    df = df.drop_duplicates(subset=["title"], keep="first")

    if TODAY_ONLY:
        today = pd.Timestamp.now().normalize()
        window_df = df[df["time"] >= today]
        window_label = f"{today:%Y-%m-%d}（当日）"
        if window_df.empty:
            # 跨日或数据未更新时兜底：退回最新一天，并明确标注
            fallback = df["time"].max().normalize()
            window_df = df[df["time"] >= fallback]
            window_label = f"{fallback:%Y-%m-%d}（非当日，数据未更新）"
    elif NEWS_WINDOW_HOURS:
        cutoff = pd.Timestamp.now() - pd.Timedelta(hours=NEWS_WINDOW_HOURS)
        window_df = df[df["time"] >= cutoff]
        window_label = f"最近 {NEWS_WINDOW_HOURS} 小时"
        if window_df.empty:
            # 长时间未更新时兜底：退回最新一天
            fallback = df["time"].max().normalize()
            window_df = df[df["time"] >= fallback]
            window_label = (
                f"{fallback:%Y-%m-%d}（已有 {NEWS_WINDOW_HOURS} 小时内无数据，数据未更新）"
            )
    else:
        window_df = df
        window_label = "全部"

    df = window_df
    day_label = window_label

    if df.empty:
        return empty, "无数据"

    df = (
        df.sort_values("time", ascending=False)
        .groupby("source", group_keys=False)
        .head(per_source)
    )
    df = df.sort_values("time", ascending=False).head(limit).reset_index(drop=True)

    df["summary"] = df["summary"].str.slice(0, SUMMARY_MAX_CHARS)
    return df, day_label


def _news_item(row) -> html.Div:
    """单条新闻：时间 + 来源标签 + 标题（可点） + 摘要"""
    stamps = row["time"]
    label = stamps.strftime("%m-%d %H:%M")
    title = html.Span(row["title"], className="fw-semibold")
    if row["link"]:
        title = html.A(
            title,
            href=row["link"],
            target="_blank",
            style={"textDecoration": "none", "color": "inherit"},
        )

    block = [
        html.Div([
            html.Small(label, className="text-muted me-2"),
            dbc.Badge(row["source"], color=row["badge"], pill=True, className="me-2"),
            title,
        ], className="d-flex align-items-center flex-wrap")
    ]
    if row["summary"]:
        block.append(
            html.P(row["summary"], className="text-muted small mb-0 mt-1")
        )
    return html.Div(block, className="border-bottom pb-2 mb-2")


news_df, news_day_label = load_news()
latest_update = (
    news_df["time"].max().strftime("%H:%M") if not news_df.empty else "无数据"
)

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

    # 快捷入口（横向一行，不再挤占新闻宽度）
    dbc.Row([
        dbc.Col([
            dbc.Button('📈 指数分析', color='primary', href='/index', size='sm', className='me-2'),
            dbc.Button('💰 金属市场', color='success', href='/metals', size='sm', className='me-2'),
            dbc.Button('🏢 行业分析', color='info', href='/industry', size='sm', className='me-2'),
            dbc.Button('📊 虚拟资产', color='warning', href='/virtual', size='sm', className='me-2'),
            dbc.Button('🔗 可转债', color='secondary', href='/bond', size='sm'),
        ], width=12, className='text-center')
    ], className='mb-3'),

    # 最新市场新闻（全宽 + 视口高度自适应）
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.Div([
                        html.H4('📰 最新市场新闻', className='mb-0'),
                        html.Small(
                            f"{len(news_df)} 条 · {news_day_label} · 按时间倒序 · 最新 {latest_update}",
                            className='text-muted',
                        ),
                    ], className='d-flex align-items-center gap-3 flex-wrap'),
                ]),
                dbc.CardBody([
                    html.Div(
                        [_news_item(row) for _, row in news_df.iterrows()],
                        style={'maxHeight': '72vh', 'overflowY': 'auto', 'padding': '10px'},
                    )
                ])
            ], className='border-0 shadow-sm')
        ], width=12)
    ]),

], fluid=True, className='py-4', style={'backgroundColor': '#f8f9fa'})
