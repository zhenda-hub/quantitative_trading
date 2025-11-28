from dash import dcc, html
import plotly.graph_objects as go
import pandas as pd
import dash
import plotly.express as px
from loguru import logger
from pathlib import Path


dash.register_page(__name__)


# 逐文件读取并对每个序列独立归一化后绘图（更接近 reits.py 的风格）
index_dir = Path("datas/raw/indexes")

# 绘制整体的归一化折线图（每个文件一个 trace）
fig = go.Figure()
for csv_file in sorted(index_dir.glob("ak_index_global_hist_em_*.csv")):
    try:
        df_tmp = pd.read_csv(csv_file)
        if "日期" in df_tmp.columns and "今开" in df_tmp.columns:
            # 解析日期并归一化今开列
            dates = pd.to_datetime(df_tmp["日期"], errors="coerce")
            vals = pd.to_numeric(df_tmp["今开"], errors="coerce")
            if vals.dropna().empty:
                continue
            vmin = vals.min()
            vmax = vals.max()
            if vmax > vmin:
                norm = (vals - vmin) / (vmax - vmin)
            else:
                norm = pd.Series(0.5, index=vals.index)

            name = csv_file.stem.replace("ak_index_global_hist_em_", "")
            fig.add_trace(go.Scatter(
                x=dates,
                y=norm,
                mode="lines",
                name=name,
                hovertemplate=(
                    "Index: " + name +
                    "<br>日期: %{x}<br>归一化值: %{y:.3f}<extra></extra>"
                )
            ))
    except Exception as e:
        logger.warning(f"读取文件 {csv_file} 失败: {e}")

fig.update_layout(
    title="全球指数归一化走势图",
    xaxis_title="日期",
    yaxis_title="归一化值 (0-1)",
    height=1000,
    template="plotly_white",
)

fig.update_xaxes(
    rangeslider_visible=True,
    minor=dict(ticks="inside", showgrid=True),
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




df = pd.read_csv("datas/processed/indexes/all_indexes_data_usd2.csv")
# breakpoint()
fig2 = px.line(
# fig = px.area(
# fig = px.scatter(
    df,
    x="date",
    y=df.columns,
    hover_data={"date": "|%B %d, %Y"},
    title='indexes chart',
    color_discrete_sequence=px.colors.qualitative.Dark24,  # Alphabet, Light24, Dark24

)
fig2.update_layout(
    height=1000,
    # xaxis_title='花萼宽度（cm）',
    yaxis_title='USD(美元)',

)
logger.debug('fig.layout.height', fig.layout.height)
logger.debug('fig.layout.width', fig.layout.width)

fig2.update_xaxes(
    # dtick="M1",
    # tickformat="%b\n%Y",
    # tickformat="%Y",
    rangeslider_visible=True,  # 添加滑动块
    minor=dict(ticks="inside", showgrid=True),  # 辅助刻度
    # 范围选择器按钮
    rangeselector=dict(
        buttons=list([
            dict(count=1, label="1month", step="month", stepmode="backward"),
            dict(count=6, label="6month", step="month", stepmode="backward"),
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




layout = html.Div(
    [
        html.H4("全球经济走势，关注变化，而不是价格"),
        html.P(
            "不同国家的股票市场指数"
            "（如上证指数、标普500、日经225、沪深300等）"
            "的单位（数值大小）并不相同，而且它们的计算方法、"
            "基期、基点也各不相同，因此直接比较指数的点数"
            "是没有意义的"
        ),
        # dcc.Checklist(
        #     id="toggle-rangeslider",
        #     options=[{"label": "Include Rangeslider", "value": "slider"}],
        #     value=["slider"],
        # ),
        # dcc.Graph(id="graph3"),


        dcc.Graph(figure=fig,),
        dcc.Graph(figure=fig2,),
    ]
)


# @callback(
#     Output("graph3", "figure"),
#     Input("toggle-rangeslider", "value"),
# )
# def display_candlestick2(value):
#     df = pd.read_csv("datas/indexes/all_indexes_data.csv")
#
#     fig = px.line(df, x="date", y=df.columns,
#                   hover_data={"date": "|%B %d, %Y"},
#                   title='custom tick labels')
#     fig.update_xaxes(
#         dtick="M1",
#         tickformat="%b\n%Y",
#         ticklabelmode="period")
#     fig.update_layout(xaxis_rangeslider_visible="slider" in value)
#     return fig


# # if __name__ == "__main__":
# #     app.run_server(debug=True)
