import dash
from dash import Dash, html
import dash_bootstrap_components as dbc

from loguru import logger
from utils.set_log import set_log
set_log('dash_web.log')

external_stylesheets = [dbc.themes.BOOTSTRAP]

app = Dash(__name__, use_pages=True, external_stylesheets=external_stylesheets)

# 硬编码的自定义导航顺序
CUSTOM_ORDER = [
    'Home', 
    'Period', 
    'Allocation', 
    "Industry",   # 行业
    'Index', 
    'Company', 
    'Bond', 
    'Virtual',
]

# 简单按自定义顺序获取页面
ordered_pages = []

real_page_name = [page['name'] for page in dash.page_registry.values()]
logger.debug(f'real_page_name: {real_page_name}')

# breakpoint()
for page_name in CUSTOM_ORDER:
    for page in dash.page_registry.values():
        # breakpoint()
        if page['name'] == page_name:
            ordered_pages.append(page)
            break
    else:
        logger.error(f'nav page {page_name} not found')
            # breakpoint()

# 使用排序后的页面或默认顺序
nav_pages = ordered_pages if ordered_pages else list(dash.page_registry.values())
# breakpoint()
app.layout = html.Div([
    dbc.NavbarSimple(
        children=[
            dbc.NavItem(dbc.NavLink(page['name'], 
                      href=page["relative_path"]))
            for page in nav_pages
        ],
        brand="Zhenda's Quantitative Trading",
        brand_href="/",
        color="primary",
        dark=True,
        fluid=True
    ),
    dash.page_container
])

if __name__ == '__main__':
    logger.info("start dash")
    app.run(debug=True)
