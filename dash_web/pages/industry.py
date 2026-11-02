import dash
from dash import Dash, dcc, html, Input, Output, callback
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import dash_bootstrap_components as dbc
from utils.chart_utils import CHART_HEIGHT

# 注册页面
dash.register_page(__name__, path='/industry')

# 读取数据
df = pd.read_csv("datas/raw/stocks/ef_行业板块.csv")
for column in ("总市值", "涨跌幅", "成交额", "换手率", "量比", "动态市盈率"):
    if column in df.columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")
df = df.dropna(subset=["总市值", "涨跌幅"])
df["涨跌幅标注"] = df["涨跌幅"].map(lambda value: f"{value:+.2f}%")

# 数据日期（不同市场交易日可能不同）
data_date = str(df["最新交易日"].iloc[0]) if "最新交易日" in df.columns else ""
rising = int((df["涨跌幅"] > 0).sum())
falling = int((df["涨跌幅"] < 0).sum())

# 行业板块树状图：面积=总市值，颜色=涨跌幅（红涨绿跌）
# 色阶范围：按实际分布 p1~p95 裁剪，避免极值把色阶拉爆导致大片近白
COLOR_RANGE = [-2.5, 6]

# 条形图只展示头尾各 TOP_N 个行业（全部 496 个会挤成一片）
TOP_N = 20
# 横向图 y 轴自下而上，升序排序后涨幅最大在最上面
top_bottom = pd.concat(
    [df.nlargest(TOP_N, "涨跌幅"), df.nsmallest(TOP_N, "涨跌幅")]
).sort_values("涨跌幅", ascending=True)

# 横向条形图高度按行数动态计算：每行 ROW_HEIGHT_PX 像素，不低于 CHART_HEIGHT
ROW_HEIGHT_PX = 16
BAR_MARGIN_HEIGHT = 120  # 标题 + 轴/边距占用的额外高度
bar_chart_height = max(
    CHART_HEIGHT, len(top_bottom) * ROW_HEIGHT_PX + BAR_MARGIN_HEIGHT
)

# 气泡图尺寸：Plotly 公式 sizeref = 2*max(size)/(标称直径²) 实际绘制直径约为标称值的 1/√2
# 标称 80 → 实际最大气泡约 56px
BUBBLE_MAX_PX = 80
BUBBLE_MIN_PX = 4

treemap_fig = px.treemap(
    df,
    path=[px.Constant("全部行业"), "股票名称"],
    values="总市值",
    color="涨跌幅",
    color_continuous_scale=["green", "#f2f2f2", "red"],
    color_continuous_midpoint=0,
    range_color=COLOR_RANGE,
    hover_data={
        "涨跌幅": ":.2f",
        "总市值": ":,.0f",
        "成交额": ":,.0f",
        "换手率": ":.2f",
    },
    title=f"行业板块市值树状图（{data_date}）面积=总市值，颜色=涨跌幅",
)
# treemap 不支持直接传 text 列, 按节点标签回填涨跌幅文字
_annotation = dict(zip(df["股票名称"], df["涨跌幅标注"]))
treemap_fig.update_traces(
    text=[_annotation.get(label, "") for label in treemap_fig.data[0].labels],
    textinfo="label+text",
    textposition="middle center",
)
treemap_fig.update_layout(
    height=CHART_HEIGHT,
    margin=dict(l=10, r=10, t=60, b=10),
    coloraxis_colorbar=dict(title="涨跌幅 %"),
)

# 创建布局
layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("行业板块分析", className="text-center my-4"),
            html.P(
                f"数据日期：{data_date}　共 {len(df)} 个行业　"
                f"上涨 {rising} 个 / 下跌 {falling} 个",
                className="text-center text-muted",
            ),
        ])
    ]),

    dbc.Row([
        dbc.Col([
            dcc.Graph(
                id='industry-treemap-chart',
                figure=treemap_fig,
            )
        ], width=12)
    ]),

    dbc.Row([
        dbc.Col([
            dcc.Graph(
                id='industry-bubble-chart',
                figure=px.scatter(
                    df,
                    x='涨跌幅',
                    y='总市值',
                    # 气泡大小 = 总市值（与 sizeref 用同一字段，否则尺度会错配）
                    size='总市值',
                    color='涨跌幅',
                    hover_name='股票名称',
                    hover_data={
                        '涨跌幅': ':.2f',
                        '总市值': ':,.0f',
                        '成交额': ':,.0f',
                    },
                    title='行业板块：涨跌幅 × 总市值（气泡大小=总市值）',
                    labels={'涨跌幅': '涨跌幅 (%)', '总市值': '总市值', '成交额': '成交额'},
                    color_continuous_scale=['green', 'lightgrey', 'red'],
                    color_continuous_midpoint=0,
                    range_color=COLOR_RANGE
                )
                .update_layout(
                    height=CHART_HEIGHT,  # 统一图表高度
                    xaxis_title='涨跌幅 (%)',
                    yaxis_title='总市值',
                    yaxis_type='log',  # 使用对数坐标，因为市值差异很大
                    showlegend=False,
                    hovermode='closest'
                )
                # 气泡缩放：sizeref 必须用 size 同字段（总市值）的 max 计算
                .update_traces(
                    marker=dict(
                        sizeref=2. * max(df["总市值"]) / (BUBBLE_MAX_PX ** 2),
                        sizemin=BUBBLE_MIN_PX,
                    )
                )
                # 添加中线
                .add_vline(x=0, line_width=1, line_dash="dash", line_color="gray")
            )
        ], width=12)
    ]),
    
    dbc.Row([
        dbc.Col([
            html.H3("行业涨跌幅排名", className="text-center my-4")
        ])
    ]),
    
    dbc.Row([
        dbc.Col([
            dcc.Graph(
                id='industry-bar-chart',
                figure=px.bar(
                    # 横向条形图：y 轴分类自下而上，升序排序后最大值在最上面
                    top_bottom,
                    x='涨跌幅',
                    y='股票名称',
                    orientation='h',
                    color='涨跌幅',
                    color_continuous_scale=['green', 'lightgrey', 'red'],
                    color_continuous_midpoint=0,
                    range_color=COLOR_RANGE,
                    title=f'行业涨跌幅排名（涨幅前 {TOP_N} + 跌幅前 {TOP_N}）',
                    labels={'涨跌幅': '涨跌幅 (%)', '股票名称': '行业名称'},
                )
                .update_layout(
                    height=bar_chart_height,  # 按行数动态计算
                    margin=dict(l=140, r=20, t=60, b=40),
                    yaxis=dict(tickfont=dict(size=9), automargin=True),
                    bargap=0.15,
                )
            )
        ], width=12)
    ]),
    dbc.Row([
        dbc.Col([
            html.H4("相关链接", className="text-center my-4"),
            dbc.Button("大盘云图", href="https://52etf.site/", 
                        external_link=True, target="_blank", color="primary"),
            # dbc.ButtonGroup([
            #     dbc.Button("东方财富", href="https://www.eastmoney.com", 
            #             external_link=True, target="_blank", color="primary"),
            #     dbc.Button("同花顺", href="https://www.10jqka.com.cn", 
            #             external_link=True, color="secondary"),
            #     dbc.Button("新浪财经", href="https://finance.sina.com.cn", 
            #             external_link=True, color="success")
            # ], className="me-3"),
            
            # dbc.ButtonGroup([
            #     dbc.Button("债券分析", href="/bond", color="info"),
            #     dbc.Button("首页", href="/", color="light"),
            #     dbc.Button("虚拟货币", href="/virtual", color="warning")
            # ])
        ], width=12, className="text-center")
    ]),
], fluid=True)
