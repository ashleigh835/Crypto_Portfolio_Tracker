import dash
import dash_bootstrap_components as dbc

# Initializes Dash application
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP,"https://use.fontawesome.com/releases/v5.12.1/css/all.css"]
    , suppress_callback_exceptions=True
    )
app.title = 'Portfolio Tracker'