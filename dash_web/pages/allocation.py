from dash import Dash, dcc, html, Input, Output, callback
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import dash
from plotly.subplots import make_subplots
# from pathlib import Path
# import sys
#
# # Build paths inside the project like this: BASE_DIR / 'subdir'.
# BASE_DIR = Path(__file__).resolve().parent.parent
# sys.path.append(str(BASE_DIR))

dash.register_page(__name__)


layout = html.Div(
    [
        html.H4("资产配置"),
        # dcc.Checklist(
        #     id="toggle-rangeslider",
        #     options=[{"label": "Include Rangeslider", "value": "slider"}],
        #     value=["slider"],
        # ),
        # dcc.Graph(id="graph_p",),
        dcc.Graph(id="graph_p2",),
        # html.Label("输入5个数据（用逗号分隔）："),
        # text = '股票'
        html.P('股票'),
        dcc.Input(
            id='input_1',
            placeholder='股票',
            type='number',
            value=1000,
            # n_blur=,
        ),
        html.P('指数基金'),
        dcc.Input(
            id='input_2',
            placeholder='指数基金',
            type='number',
            value=1000
        ),
        html.P('债券'),
        dcc.Input(
            id='input_3',
            placeholder='债券',
            type='number',
            value=1000
        ),
        html.P('货币基金'),
        dcc.Input(
            id='input_4',
            placeholder='货币基金',
            type='number',
            value=1000
        ),

        # html.Button('Submit', id='submit-button-state'),

        # dcc.Graph(figure=go.Figure(data=[go.Pie(values=[1,2,3,4], labels=['a','b','c','d'])])
        #           # px.pie(values=[1,2,3,4], labels=['a','b','c','d'],
        #           # # hover_data={"date": "|%B %d, %Y"},
        #           # title='person allocation')
        # ),
    ]
)


# @callback(
#     Output("graph_p", "figure"),
#     Input("input_1", "value"),
#     Input("input_2", "value"),
#     Input("input_3", "value"),
#     Input("input_4", "value"),
# )
# def display_alloc(*args, **kwargs):
#     # "https://raw.githubusercontent.com/plotly/datasets/master/finance-charts-apple.csv"
#     # df = pd.read_csv("datas/indexes/all_indexes_data.csv")
#     # breakpoint()
#     labels = ['股票', '指数基金', '债券', '货币基金']
#     df = pd.DataFrame(dict(
#         labels=labels,
#         category=['激进', '激进', '稳定', '稳定'],
#         values=list(args)
#     ))
#     print('df', df)
#
#     fig = px.sunburst(df, path=['category', 'labels'], values='values')
#     # fig = px.sunburst(df, path=['category', 'labels'], values='values', color='labels')
#
#     fig.update_layout(
#         title=f'资产配置旭日图， 总计: {sum(args)}',
#         height=600,
#     )
#     return fig


@callback(
    Output("graph_p2", "figure"),
    Input("input_1", "value"),
    Input("input_2", "value"),
    Input("input_3", "value"),
    Input("input_4", "value"),
)
def display_alloc2(*args, **kwargs):
    # "https://raw.githubusercontent.com/plotly/datasets/master/finance-charts-apple.csv"
    # df = pd.read_csv("datas/indexes/all_indexes_data.csv")
    # breakpoint()
    labels = ['股票', '指数基金', '债券', '货币基金']
    df = pd.DataFrame(dict(
        labels=labels,
        category=['激进', '激进', '稳定', '稳定'],
        values=list(args)
    ))
    print('df', df)

    # fig = go.Figure(data=[go.Pie(values=list(args), labels=labels)])
    fig = px.pie(
        df,
        values='values',
        names='labels',
        hover_data=['category']
    )
    fig.update_traces(textinfo='percent+value')  # 设置显示内容
    # fig.update_traces(textposition='inside')

    fig.update_layout(
        title=f'资产配置饼图， 总计: {sum(args)}',
        height=600,
    )
    return fig

# # if __name__ == "__main__":
# #     app.run_server(debug=True)
