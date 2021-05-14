import sys
sys.path.append('../')
from app import app

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

import pandas as pd
import plotly.graph_objects as go
import plotly.colors as pc


exchange_dropdown = dcc.Dropdown(
    id = 'exchange',
    options=[
        {'label': 'Kraken', 'value': 'kraken'},
        {'label': 'Coinbase', 'value': 'coinbase'},
    ],
    value='kraken',
    multi=False
)


balances_content = [   
    dbc.Row(
        [dbc.Col(exchange_dropdown,align='center')],
        align='center',
        no_gutters = True,
        style={"width": "10%",'padding-top':'3%','padding-left':'1%'}
    ),
]
prices_content = balances_content
transactions_content = balances_content

tab_Style = {
    'padding': '0',
    'height': '44px',
    'line-height': '44px'
}

layout = html.Div(
    [   dcc.Tabs(
            id='tab', 
            value='home', 
            children=[
                dcc.Tab(label='Balances', value='bal',style=tab_Style,selected_style=tab_Style),
                dcc.Tab(label='Prices', value='price',style=tab_Style,selected_style=tab_Style),
                dcc.Tab(label='Transactions', value='trans',style=tab_Style,selected_style=tab_Style),
            ],
        ),
        html.Div(id='tab-content')
    ]
)

@app.callback(Output('tab-content', 'children'),
              Input('tab', 'value'))
def render_content(tab):
    if tab == 'bal':
        return html.Div(balances_content)
    elif tab == 'price':
        return html.Div(prices_content)
    elif tab == 'trans':
        return html.Div(transactions_content)


if __name__ == '__main__':
    app.layout = layout
    app.run_server(debug=True)