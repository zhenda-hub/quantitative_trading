import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd

# 假设你有行业数据的DataFrame，这里用随机数据代替
df = pd.DataFrame({
    'Date': pd.date_range('2023-01-01', '2023-01-10'),
    'Industry1': [10, 12, 8, 15, 11, 9, 14, 13, 16, 10],
    'Industry2': [8, 11, 14, 10, 13, 12, 9, 15, 10, 11],
})

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("行业数据涨跌图表"),
    dcc.Graph(id='industry-chart'),
    dcc.RangeSlider(
        id='date-range',
        marks={i: date.strftime('%Y-%m-%d') for i, date in enumerate(df['Date'])},
        min=0,
        max=len(df['Date']) - 1,
        value=[0, len(df['Date']) - 1],
        step=1,
        allowCross=False
    )
])

@app.callback(
    Output('industry-chart', 'figure'),
    [Input('date-range', 'value')]
)
def update_chart(selected_dates):
    filtered_df = df.iloc[selected_dates[0]: selected_dates[1] + 1]

    fig = px.line(filtered_df, x='Date', y=df.columns[1:], title='行业数据涨跌图表')
    fig.update_layout(
        xaxis_title='日期',
        yaxis_title='行业数据',
        legend_title='行业',
    )

    return fig

if __name__ == '__main__':
    app.run_server(debug=True)