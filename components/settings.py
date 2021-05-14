
import json
from datetime import datetime

import sys
sys.path.append('../')
from app import app

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash
from dash.dependencies import Input, Output, State, ALL
from dash.exceptions import PreventUpdate

from Crypto_Portfolio_Tracker.lib.dash_functions import load_settings, add_to_json, remove_entry_from_json, get_latest_index_from_json


def generate_individual_wallet_listgroup(wallets,section):
    ls=[]
    for wallet in wallets:
        ls+=[   
            dbc.ListGroupItem(
                [   dbc.Row(
                        [   dbc.Col(html.P(f"Added {wallet['time_added']}",className="card-text")),
                            dbc.Col(
                                dbc.Button(children=[html.I(className="fas fa-minus-square", style={'color':'red'})], size='sm', color='link',
                                    style={'margin':'0',"padding":"0",'background-color': 'white', 'float':'right','align':'center'},
                                    id={'index':wallet['id'],'type':f'remove-{section}'}
                                ),
                                style={'padding-right':'1%'}    
                            ),
                        ]
                    )
                ]
            )
        ]
    return ls

def generate_wallet_card_body(wallets, section):
    ls=[]
    for wallet_type in wallets:
        ls+=dbc.CardBody(
            [   dbc.CardHeader(wallet_type,style={'background-color': 'white', 'font-weight': 'bold'}),
                dbc.ListGroup(
                    generate_individual_wallet_listgroup(wallets[wallet_type], section),
                    flush=True,
                ),
            ]
        ),
    return ls

def generate_wallet_card_header(header, section):
    return [
        header,
        dbc.Button(children=[html.I(className="fas fa-plus-square", style={'color':'green'})], id=f'add-{section}-modal', size='sm', color='link',
            style={'margin':'0',"padding":"0",'background-color': 'light', 'float':'right'}
        )
    ]
def generate_wallet_content(wallets, section):
    if len(wallets) == 0:
        return html.P(f"Looks like you haven't added any {section} yet! Click to Add", className="card-text")
    else:
        if section == 'APIs':
            return dbc.Card(generate_wallet_card_body(wallets,section))
        else:
            return generate_wallet_card_body(wallets,section)

def generate_wallet_cards(wallet_data):
    section_titles = {'APIs' : "Exchange Wallets", 'Addresses': "Address Wallets"}
    cards = []
    for section in wallet_data:
        if section == 'APIs':
            main_exchange_wallet_header = generate_wallet_card_header(section_titles[section],section)
            exchange_wallet_card_body = generate_wallet_content(wallet_data[section],section)
            cards += [
                dbc.Card(
                    [   dbc.CardHeader(main_exchange_wallet_header),
                        dbc.CardBody(exchange_wallet_card_body),
                    ]
                )
            ]
        else:
            main_exchange_wallet_header = generate_wallet_card_header(section_titles[section],section)
            exchange_wallet_card_body = generate_wallet_content(wallet_data[section],section)
            cards += [
                dbc.Card(
                    [   dbc.CardHeader(main_exchange_wallet_header),
                        dbc.CardBody(exchange_wallet_card_body),
                    ]
                )
            ]
        cards += [API_modal]
    return cards

exchange_dropdown = dcc.Dropdown(
    id = 'exchange',
    options=[
        {'label': 'Kraken', 'value': 'Kraken'},
        {'label': 'Coinbase', 'value': 'Coinbase'},
    ],
    multi=False,
    value='Kraken'
)
asset_dropdown = dcc.Dropdown(
    id = 'asset-dd',
    options=[
        {'label': 'Doge', 'value': 'Doge'},
        {'label': 'Bitcoin', 'value': 'BTC'},
        {'label': 'Monero', 'value': 'XMR'},
    ],
    multi=False,
    value='BTC'
)

API_modal = html.Div(
    [   dbc.Modal(
            [   dbc.ModalHeader("Add Addresses"),
                dbc.ModalBody(
                    [   dbc.FormGroup(asset_dropdown),
                        dbc.FormGroup(
                            [   dbc.Label("Address", html_for="wallet-address", width = 2, style={'padding':'2%'}),
                                dbc.Col(
                                    [   dbc.Input(type="text", id="wallet-address"),
                                        dbc.FormFeedback("Address required", valid=False),
                                    ],
                                    align = 'center'
                                )
                            ],
                            row=True,
                        ),
                    ]
                ),
                dbc.ModalFooter(
                    [   dbc.ButtonGroup(
                            [   dbc.Button("Add", id="add-addresses", className="ml-auto",color='success'),
                                dbc.Button("Cancel", id="Addresses-close", className="ml-auto")
                            ],
                            size="sm",
                        ),
                    ]
                ),
            ],
            id="Addresses-modal",
            size="lg",
            centered=True,
            is_open=False),
        dbc.Modal(
            [   dbc.ModalHeader("Add API"),
                dbc.ModalBody(
                    dbc.Form(
                        [   dbc.FormGroup(exchange_dropdown),
                            dbc.FormGroup(
                                [   dbc.Label("API Key", html_for="api-key", width = 2, style={'padding':'2%'}),
                                    dbc.Col(
                                        [   dbc.Input(type="text", id="api-key"),
                                            dbc.FormFeedback("API Key required", valid=False),
                                        ],
                                        align = 'center'
                                    )
                                ],
                                row=True,
                            ),
                            dbc.FormGroup(
                                [   dbc.Label("API Secret", html_for="api-sec", width = 2, style={'padding':'2%'}),
                                    dbc.Col(
                                        [   dbc.Input(type="text", id="api-sec"),
                                            dbc.FormFeedback("API Secret required", valid=False),
                                        ],
                                        align = 'center',
                                    )
                                ],
                                row=True,
                            ),
                            dbc.FormGroup(
                                [   dbc.Label("API Passphrase", html_for="api-pass", width = 2, style={'padding':'2%'}),
                                    dbc.Col(
                                        [   dbc.Input(type="text", id="api-pass"),
                                            dbc.FormText("Not all exchanges require an API Passphrase - leave blank if not required",color="secondary")
                                        ],
                                        align = 'center'
                                    )
                                ],
                                row=True,
                            ),
                        ]
                    )
                ),
                dbc.ModalFooter(
                    [   dbc.ButtonGroup(
                            [   dbc.Button("Add", id="add-api", className="ml-auto",color='success'),
                                dbc.Button("Cancel", id="API-close", className="ml-auto")
                            ],
                            size="sm",
                        ),
                    ]
                ),
            ],
            id="APIs-modal",
            size="lg",
            centered=True,
            is_open=False
        ),
    ]
)

tab_Style = {
    'padding': '0',
    'height': '44px',
    'line-height': '44px'
}

layout = html.Div(
    [   dcc.Store(data=load_settings(), id='memory', storage_type='session'),
    # [   dcc.Store(id='memory', storage_type='session', clear_data =True),
        dcc.Tabs(
            id='tab_settings', 
            value='Wallet', 
            children=[
                dcc.Tab(label='Wallet Settings', value='Wallet',style=tab_Style,selected_style=tab_Style),
                dcc.Tab(label='User Settings', value='User',style=tab_Style,selected_style=tab_Style),
            ],
        ),
        html.Hr(),
        html.Div(id='tab-content-settings')
    ]
)

wallet_content = html.Div(id='wallet')

@app.callback(Output('tab-content-settings', 'children'),
              Input('tab_settings', 'value')
    )
def render_tab_content(tab):
    app.logger.info(f'running render_tab_content on {tab}')
    if tab == 'Wallet':
        return wallet_content
    if tab == 'User':
        return html.Div("COMING SOON!")

@app.callback(Output('wallet', 'children'),
              Input('memory', 'data'))
def load_wallet_data(data):
    if data is not None:
        app.logger.info(f'running load_wallet_data on {data.keys()}')
        return generate_wallet_cards(data['Wallets'])
    else:
        raise PreventUpdate

@app.callback(
    Output("APIs-modal", "is_open"),
    [   Input("add-APIs-modal", "n_clicks"), 
        Input("API-close", "n_clicks")
    ]
)
def toggle_API_modal(n1,n2):
    ctx = dash.callback_context
    if (len(ctx.triggered)>0) & ([n1,n2] != [None]*2):
        trg = ctx.triggered[0]['prop_id'].split('.')[0]  
        if trg == "add-APIs-modal":
            return True
        elif trg == "API-close":
            return False
    else:
        raise PreventUpdate

@app.callback(
    Output("Addresses-modal", "is_open"),
    [   Input("add-Addresses-modal", "n_clicks"), 
        Input("Addresses-close", "n_clicks")
    ]
)
def toggle_Addresses_modal(n1,n2):
    ctx = dash.callback_context
    if (len(ctx.triggered)>0) & ([n1,n2] != [None]*2):
        trg = ctx.triggered[0]['prop_id'].split('.')[0]  
        if trg == "add-Addresses-modal":
            return True
        elif trg == "Addresses-close":
            return False
    else:
        raise PreventUpdate

@app.callback( 
    Output('wallet-address','invalid'), 
    Output('api-key','invalid'), 
    Output('api-sec','invalid'),
    Output('memory', 'data'),
    Input('add-api', 'n_clicks'),
    Input('add-addresses', 'n_clicks'),
    Input({'type': 'remove-APIs', 'index': ALL}, 'n_clicks'),
    Input({'type': 'remove-Addresses', 'index': ALL}, 'n_clicks'),
    [   State('exchange', 'value'),
        State('api-key', 'value'),
        State('api-sec', 'value'),
        State('api-pass', 'value'),
        State('asset-dd', 'value'),
        State('wallet-address', 'value'),
    ]
    , prevent_initial_call = True
)
def add_or_remove_API(n1, n2, n3, n4, exchange, api_key, api_sec, api_pass, asset, address):
    ctx = dash.callback_context
    bad_api_key = False
    bad_api_sec = False 
    bad_address = False
    # app.logger.info([n1,n2]+n3+n4)
    # app.logger.info([None]*2+[None]*len(n3)+[None]*len(n4))
    # app.logger.info([None]*(2+len(n3)+len(n4)))
    # if (len(ctx.triggered)>0) & (([n1,n2]+n3+n4) != ([None]*2+[None]*len(n3)+[None]*len(n4))):
    #     app.logger.info( (len(ctx.triggered)>0) & (([n1,n2]+n3+n4) != ([None]*2+[None]*len(n3)+[None]*len(n4))) )
    if (len(ctx.triggered)>0) & (([n1,n2]+n3+n4) != ([None]*(2+len(n3)+len(n4)))):
        trg = ctx.triggered[0]['prop_id'].split('.')[0]
        if trg == 'add-api':
            if api_key in [None,'']:
                bad_api_key = True
            if api_sec in [None,'']:
                bad_api_sec = True

            if bad_api_key == bad_api_sec == False:
                max_index = get_latest_index_from_json('APIs')

                exch = {
                    exchange : {
                        'id' : max_index,
                        'api_key' : api_key,
                        'api_sec' : api_sec,
                        'api_pass' : api_pass,
                        'time_added': datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    }
                }
                app.logger.info(f"adding entry {exch} to json")
                add_to_json(type='APIs', dta=exch)
                return bad_address, bad_api_key, bad_api_sec, load_settings()

            return bad_address, bad_api_key, bad_api_sec, None
        elif trg == 'add-addresses':
            if address in [None,'']:
                bad_address = True
                
            else:
                max_index = get_latest_index_from_json('Addresses')

                addr = {
                    asset : {
                        'id' : max_index,
                        'address' : address,
                        'time_added': datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    }
                }  
                app.logger.info(f"adding entry {addr} to json")
                add_to_json(type='Addresses', dta=addr)
                return bad_address, bad_api_key, bad_api_sec, load_settings()  
            return bad_address, bad_api_key, bad_api_sec, None

        else:
            trg_dta = json.loads(trg)
            app.logger.info(f"attempt to remove {trg}")
            app.logger.info(remove_entry_from_json(trg_dta['index'],trg_dta['type'].split('-')[1]))
            return bad_address, bad_api_key, bad_api_sec, load_settings()
    else:
        raise PreventUpdate

if __name__ == '__main__':
    app.layout = layout
    app.run_server(debug=True)