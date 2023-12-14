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
        height=1000,
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

    return fig


fig_gdp = gene_fig("datas/gdps/all_gdps_data.csv", 'GDP年率', 'GDP年率')
fig_cpi = gene_fig("datas/cpis/all_cpi_data.csv", 'CPI年率', 'CPI年率(e.g., 数值为2.5，意味着物价一年涨2.5%)')
fig_unemp = gene_fig("datas/unemps/all_unemps_data.csv", '失业率', '失业率')


layout = html.Div(
    [
        html.H4("全球经济周期"),
        html.H6("GDP年率，经济发展状况"),
        html.H6("CPI年率，反应物价波动状况， 通常和GDP成正方向"),
        html.H6("失业率， 经济周期中，通常和GDP，CPI成反方向"),
        html.H6("GDP， CPI表示经济周期：上升，高点，下降，低点"),
        # dcc.Checklist(
        #     id="toggle-rangeslider",
        #     options=[{"label": "Include Rangeslider", "value": "slider"}],
        #     value=["slider"],
        # ),
        # dcc.Graph(id="graph3"),


        dcc.Graph(figure=fig_gdp,),
        dcc.Graph(figure=fig_cpi,),
        dcc.Graph(figure=fig_unemp,),
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
