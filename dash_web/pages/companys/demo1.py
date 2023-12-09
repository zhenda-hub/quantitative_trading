from dash import Dash, dcc, html, Input, Output, callback
import plotly.graph_objects as go
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

layout = html.Div(
    [
        html.H4("google stock candlestick chart"),
        dcc.Checklist(
            id="toggle-rangeslider",
            options=[{"label": "Include Rangeslider", "value": "slider"}],
            value=["slider"],
        ),
        dcc.Graph(id="graph"),
    ]
)


@callback(
    Output("graph", "figure"),
    Input("toggle-rangeslider", "value"),
)
def display_candlestick(value):
    # "https://raw.githubusercontent.com/plotly/datasets/master/finance-charts-apple.csv"
    df = pd.read_excel("datas/stocks/gegu_stock_ak.xlsx")

    fig = go.Figure(
        go.Candlestick(
            x=df["date"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
        )
    )
    fig.update_layout(xaxis_rangeslider_visible="slider" in value)
    return fig


# if __name__ == "__main__":
#     app.run_server(debug=True)
