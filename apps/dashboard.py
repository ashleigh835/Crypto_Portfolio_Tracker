from app import app

from config import fiat_currencies
from lib.dash_functions import generate_balance_table
from lib.functions import balances_from_dict
from lib.API_functions import fetch_daily_price_pairs

import pandas as pd
import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

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

balances_content = html.Div(
    [   html.Div(dbc.Spinner(color='secondary'), style={'position':'fixed','top':'20%','left':'50%'})
    ], id='balances-info'
)

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
    [   dcc.Store(id='daily-prices-df', storage_type='session'),
        dcc.Store(id='balance-df', storage_type='session', clear_data=True),
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
    Input('memory', 'data'),Input('encryption-key-set','data'),
    State('encryption-key','data'),State('balance-df','data'),State('daily-prices-df','data'), 
    prevent_initial_call = True
)
def load_balance_data(data, key_set, stored_key, balance_df, daily_prices_df):
    """
    updates the balance dataframe

    Args:
        data (dict): stored in the id 'memory'
        stored_key (str): stored decryption key
        key_set (bool): whether the key has been set or not, stored in the dcc.Store method
        balance-df (pandas.DataFrame): Stored Dataframe with balances data from Wallets

    Raises:
        PreventUpdate: doesn't update if data is empty

    Returns:
        json: json panda dataframe object of the balance dataframe
    """
    ctx = dash.callback_context
    trg = ctx.triggered[0]['prop_id'].split('.')[0]  
    if data is not None:
        if key_set:
            if (balance_df is None) | (daily_prices_df is None) | (trg not in [None,'']):
                df = balances_from_dict(data['Wallets'],stored_key.encode())
                df = df.sort_values('Total', ascending=False)
                # df = df.reset_index().rename(columns={'index':''}).sort_values('Total', ascending=False)

                if daily_prices_df is not None:
                    daily_prices_df = pd.read_json(daily_prices_df)
                    dta = daily_prices_df.columns
                else:
                    dta = []
                    daily_prices_df = pd.DataFrame()

                pairs = [f"{li}/USD" for li in df[~df.index.isin(fiat_currencies)].index.sort_values().drop_duplicates()]
                # pairs = [f"{li}/USD" for li in df[~df[''].isin(fiat_currencies)][''].sort_values().drop_duplicates()]

                daily_prices_df, dta = fetch_daily_price_pairs(pairs,'kraken',dta, daily_prices_df)
                daily_prices_df, dta = fetch_daily_price_pairs(pairs,'coinbase',dta, daily_prices_df)

                return df.to_json(), daily_prices_df.to_json()
    return balance_df, daily_prices_df

@app.callback(Output('balances-info', 'children'),Input('balance-df','data'),State('daily-prices-df','data'),State('encryption-key-set','data'))
def render_balance_data(balance_df,daily_prices_df,key_set):
    """
    render the balance data from the stored json dataframe file

    Args:
        balance-df (pandas.DataFrame): Stored Dataframe with balances data from Wallets
        key_set (bool): whether the key has been set or not, stored in the dcc.Store method

    Returns:
        html children: creates a dash table from the stored data
    """
    ctx = dash.callback_context
    app.logger.info(ctx.triggered)
    if balance_df is not None:
        if key_set:
            df = pd.read_json(balance_df)
            prices_df = pd.read_json(daily_prices_df)
            app.logger.info(prices_df.tail(1))
            # return dbc.Table.from_dataframe(df, striped=True, bordered=False, hover=True, style={'text-align':'center'})
            return generate_balance_table(df,prices_df)

if __name__ == '__main__':
    import sys
    sys.path.append('../')
    
    app.layout = layout
    app.run_server(debug=True)