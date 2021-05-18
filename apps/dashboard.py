from app import app

from lib.dash_functions import generate_balance_table
from lib.functions import balances_from_dict

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

# exchange selection - hardcoded options for now
exchange_dropdown = dcc.Dropdown(
    id = 'exchange',
    options=[
        {'label': 'Kraken', 'value': 'kraken'},
        {'label': 'Coinbase', 'value': 'coinbase'},
    ],
    value='kraken',
    multi=False
)

# content style when the balances tab is selected - for now duplicate for the prices and transactions
balances_content = html.Div(
    html.Div(dbc.Spinner(color='secondary'), style={'position':'fixed','top':'20%','left':'50%'}), id='balances-info')

prices_content = [   
    dbc.Row(
        [dbc.Col(exchange_dropdown,align='center')],
        align='center',
        no_gutters = True,
        style={"width": "10%",'padding-top':'3%','padding-left':'1%'}
    ),
]
transactions_content = [   
    dbc.Row(
        [dbc.Col(exchange_dropdown,align='center')],
        align='center',
        no_gutters = True,
        style={"width": "10%",'padding-top':'3%','padding-left':'1%'}
    ),
]


# default style for the tab & selected tab
tab_Style = {
    'padding': '0',
    'height': '44px',
    'line-height': '44px'
}

# dashboard layout
layout = html.Div(
    [   dcc.Tabs(
            id='db-tab', 
            value='bal', 
            children=[
                dcc.Tab(label='Balances', value='bal',style=tab_Style,selected_style=tab_Style),
                dcc.Tab(label='Prices', value='price',style=tab_Style,selected_style=tab_Style),
                dcc.Tab(label='Transactions', value='trans',style=tab_Style,selected_style=tab_Style),
            ],
        ),
        html.Hr(),
        html.Div(id='db-tab-content')
    ]
)

@app.callback(Output('db-tab-content', 'children'),
              Input('db-tab', 'value'))
def render_content(tab):
    """
    Render tab content based on the selected tab

    Args:
        tab (str): string value associated with the id: db-tab

    Returns:
        html: html content based on tab selected
    """    
    if tab == 'bal':
        return balances_content
    elif tab == 'price':
        return html.Div(prices_content)
    elif tab == 'trans':
        return html.Div(transactions_content)

@app.callback(Output('balances-info', 'children'),Input('memory', 'data'),Input('encryption-key','data'),State('encryption-key-set','data'))
def load_balance_data(data, stored_key, key_set ):
    """
    trigger when the stored data for id 'memory' changes and updates the children of the tab_content

    Args:
        data (dict): stored in the id 'memory'
        stored_key (str): stored decryption key
        key_set (bool): whether the key has been set or not, stored in the dcc.Store method

    Raises:
        PreventUpdate: doesn't update if data is empty

    Returns:
        list: list of html children containing cards of wallets
    """
    if data is not None:
        if key_set:
            df = balances_from_dict(data['Wallets'],stored_key.encode())
            df = df.reset_index().rename(columns={'index':''}).sort_values('Total', ascending=False)
            return dbc.Table.from_dataframe(df, striped=True, bordered=False, hover=True)
            # return generate_balance_table(df)
            # return generate_wallet_cards(data['Wallets'],stored_key.encode())
        # else:
            # return generate_wallet_cards(data['Wallets'],'')
    else:
        raise PreventUpdate

if __name__ == '__main__':
    import sys
    sys.path.append('../')
    
    app.layout = layout
    app.run_server(debug=True)