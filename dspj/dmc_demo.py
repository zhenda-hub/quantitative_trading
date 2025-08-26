import dash_mantine_components as dmc
from dash import Dash

app = Dash()

app.layout = dmc.MantineProvider(
    dmc.Alert(
       "Welcome to Dash Mantine Components",
       title="Hello!",
       color="violet",
    )
)

if __name__ == "__main__":
    app.run(debug=True)