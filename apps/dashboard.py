from app import app

from config import fiat_currencies

from lib.dash_functions import generate_balance_table
from lib.functions import balances_from_dict, pull_spot_prices_from_all_sources

import pandas as pd
import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from datetime import datetime

# exchange selection - hardcoded options for now
exchange_dropdown = dcc.Dropdown(
    id = 'exchange',
    options=[
        {'label': 'Kraken', 'value': 'kraken'},
        {'label': 'Coinbase', 'value': 'coinbase'},
        {'label': 'Bittrex', 'value': 'bittrex'},
    ],
    value='kraken',
    multi=False
)

balances_content =[   
    html.Div(
        dbc.Checklist(
            options=[{"label": "Group Same-Asset Wallet Addresses", "value": 1}],
            value=[1],
            id="group-addresses",
            switch=True
        )
        , style={'padding-left':'1%','padding-bottom':'1%'}
    ),
    html.Div(
        [   html.Div(dbc.Spinner(color='secondary'), style={'position':'fixed','top':'20%','left':'50%'})
        ], id='balances-info'
    )
]

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
    [   dcc.Store(id='daily-prices-df', storage_type='session',clear_data=True),
        dcc.Store(id='balance-df', storage_type='session'),
        dcc.Tabs(
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

@app.callback(
    Output('balance-df','data'),Output('daily-prices-df','data'),
    Input('memory', 'data'), Input('encryption-key-set','data'),
    State('encryption-key','data'),State('balance-df','data'),State('daily-prices-df','data'), 
    prevent_initial_call = True
)

def load_balance_data(data, key_set, stored_key, balance_df, daily_prices_df):
    """
    updates the balance dataframe

    Args:
        data (dict): stored in the id 'memory'
        key_set (bool): whether the key has been set or not, stored in the dcc.Store method
        stored_key (str): stored decryption key
        balance_df (pandas.DataFrame): Stored Dataframe with balances data from Wallets
        daily_prices_df (pandas.DataFrame): Stored Dataframe with prices for listed assets

    Raises:
        PreventUpdate: doesn't update if data is empty

    Returns:
        json: json panda dataframe object of the balance dataframe
        json: json panda dataframe object of the prices dataframe
    """

    native = 'USD'
    ctx = dash.callback_context
    trg = ctx.triggered[0]['prop_id'].split('.')[0]  
    if data is not None:
        if key_set:
            if (balance_df is None) | (daily_prices_df is None) | ((trg not in [None,'']) & (len(ctx.triggered)==1)):
                print(f"loading_balance_data! Triggered: {trg} (triggers: {len(ctx.triggered)})")
                print(f"trigger reason: {balance_df is None} | {daily_prices_df is None} | ({trg not in [None,'']} & {len(ctx.triggered)==1})")

                # import json
                # with open("data_file.json", "w") as write_file:
                #     json.dump(data, write_file, indent=4)

                bal_df = balances_from_dict(data['Wallets'],stored_key.encode())
                # bal_df = pd.read_json(balance_df)          
                bal_df = bal_df.sort_values('Total', ascending=False)      

                if daily_prices_df is not None:
                    daily_prices_df = pd.read_json(daily_prices_df)
                else:
                    daily_prices_df = pd.DataFrame()

                native='USD'
                price_symbols = [bal for bal in bal_df.index.values if bal != native]
                daily_prices_df = pull_spot_prices_from_all_sources(price_symbols, data, native=native, spot_df=daily_prices_df)

                return bal_df.to_json(), daily_prices_df.to_json()
                # return balance_df, daily_prices_df.to_json()
    return balance_df, daily_prices_df

@app.callback(Output('balances-info', 'children'),Input('balance-df','data'),Input('group-addresses','value'),State('daily-prices-df','data'),State('encryption-key-set','data'), 
    prevent_initial_call = True)
def render_balance_data(balance_df,group_addresses,daily_prices_df,key_set):
    """
    render the balance data from the stored json dataframe file

    Args:
        balance-df (pandas.DataFrame): Stored Dataframe with balances data from Wallets
        group_addresses (int): Radio button indicator for whether same-asset wallets should be grouped (default opted in on page)
        key_set (bool): whether the key has been set or not, stored in the dcc.Store method
        daily_prices_df (pandas.DataFrame): Stored Dataframe with prices for listed assets

    Returns:
        html children: creates a dash table from the stored data
    """
    if balance_df is not None:
        if key_set:
            group_rule = False
            if group_addresses == [1]:
                group_rule=True
            bal_df = pd.read_json(balance_df)
            prices_df = pd.read_json(daily_prices_df)

            # return dbc.Table.from_dataframe(bal_df, striped=True, bordered=False, hover=True, style={'text-align':'center'})
            return generate_balance_table(bal_df,prices_df,'USD',group_rule)

if __name__ == '__main__':
    import sys
    sys.path.append('../')
    
    app.layout = layout
    app.run_server(debug=True)