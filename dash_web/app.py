import dash
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc

from loguru import logger
from utils.set_log import set_log
set_log()

external_stylesheets = [dbc.themes.BOOTSTRAP]

app = Dash(__name__, use_pages=True, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    html.H1("Zhenda's quan"),
    # dbc.Row(
    #     [
    #         dbc.Col(
    #             [
    #                 html.Div(
    #                     dcc.Link(
    #                         f"{page['name']} - {page['path']}", href=page["relative_path"]
    #                     ),
    #
    #                 )
    #                 for page in dash.page_registry.values()
    #             ],
    #             width=3
    #         ),
    #         dbc.Col(
    #             dash.page_container,
    #             width=9
    #         ),
    #     ]
    # ),

    html.Div([
        html.Div(
            dcc.Link(f"{page['name']} - {page['path']}", href=page["relative_path"])
            # dcc.Link(f"{page['name']}", href=page["relative_path"])
        ) for page in dash.page_registry.values()  # TODO: set title
    ]),
    dash.page_container
])

if __name__ == '__main__':
    logger.info("start dash")
    app.run(debug=True)