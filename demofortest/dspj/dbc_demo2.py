import dash
import dash_bootstrap_components as dbc
from dash import html, dcc
import plotly.express as px

# 准备数据和图表
df = px.data.iris()
fig = px.scatter(df, x="sepal_width", y="sepal_length", color="species")

# 创建 Dash app，使用 Bootstrap 主题
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# 页面布局
app.layout = dbc.Container(
    [
        html.H1("Iris Dataset Visualization", className="text-center my-4"),
        dcc.Graph(figure=fig)  # 显示 Plotly 图
    ],
    fluid=True
)

if __name__ == "__main__":
    app.run(debug=True)
