from dash import Dash, dcc, html, Input, Output, callback
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import dash
# from pathlib import Path
# import sys
#
# # Build paths inside the project like this: BASE_DIR / 'subdir'.
# BASE_DIR = Path(__file__).resolve().parent.parent
# sys.path.append(str(BASE_DIR))

dash.register_page(__name__)
# app = Dash(__name__, use_pages=True, pages_folder="my_apps")

df = pd.read_csv("datas/processed/virtual/all_virtual_data.csv")
# breakpoint()
fig = px.line(
    df,
    x="date",
    y=df.columns,
    hover_data={"date": "|%B %d, %Y"},
    title='virtual chart',

)
fig.update_layout(
    height=1000,
    # xaxis_title='花萼宽度（cm）',
    yaxis_title='USD(美元)',

)
print('fig.layout.height', fig.layout.height)
print('fig.layout.width', fig.layout.width)

fig.update_xaxes(
    # dtick="M1",
    # tickformat="%b\n%Y",
    # tickformat="%Y",
    rangeslider_visible=True,  # 添加滑动块
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
        html.H4("加密货币走势，关注变化，而不是价格"),
        # dcc.Checklist(
        #     id="toggle-rangeslider",
        #     options=[{"label": "Include Rangeslider", "value": "slider"}],
        #     value=["slider"],
        # ),
        # dcc.Graph(id="graph3"),


        dcc.Graph(figure=fig,),
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
