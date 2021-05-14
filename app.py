import dash
import dash_bootstrap_components as dbc

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP,"https://use.fontawesome.com/releases/v5.12.1/css/all.css"]
    , suppress_callback_exceptions=True
    )
app.title = 'Portfolio Tracker'

from lib import dash_functions as df
app_settings = df.load_settings()