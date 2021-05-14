from Crypto_Portfolio_Tracker.lib.dash_functions import load_settings, add_to_json

import sys
sys.path.append('../')
from app import app

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from datetime import datetime

def generate_wallet_cards(apis):

    main_exchange_wallet_header = [
        "Exchange Wallets",
        dbc.Button(children=[html.I(className="fas fa-plus-square", style={'color':'green'})], id='add-API-modal', size='sm', color='link',
            style={'margin':'0',"padding":"0",'background-color': 'light', 'float':'right'}
        )
    ]



    def generate_individual_apis_listgroup(exchange):
        ls=[]
        i=0
        for api in apis[exchange]:
            ls+=[   
                dbc.ListGroupItem(
                    [   dbc.Row(
                            [   dbc.Col(html.P(f"API added {api['time_added']}",className="card-text")),
                                dbc.Col(
                                    dbc.Button(children=[html.I(className="fas fa-minus-square", style={'color':'red'})], id='remove-api-{i}', size='sm', color='link',
                                        style={'margin':'0',"padding":"0",'background-color': 'white', 'float':'right','align':'center'}
                                    ),
                                    style={'padding-right':'1%'}    
                                ),
                            ]
                        )
                    ]
                )
            ]
            i+=1
        return ls

    def generate_exchange_card(apis):
        ls=[]
        for exchange in apis:
            ls+=dbc.CardBody(
                [   dbc.CardHeader(exchange,style={'background-color': 'white', 'font-weight': 'bold'}),
                    dbc.ListGroup(
                        generate_individual_apis_listgroup(exchange),
                        flush=True,
                    ),
                ]
            ),
        return ls

    if len(apis) == 0:
        exchange_wallet_card_body = html.P("Looks like you haven't added any APIs yet! Click to Add", className="card-text")
    else:
        exchange_wallet_card_body = dbc.Card(generate_exchange_card(apis))
        # exchange_wallet_card_body = generate_exchange_card(apis)
    
    return [
        dbc.Card(
            [   dbc.CardHeader(main_exchange_wallet_header),
                dbc.CardBody(exchange_wallet_card_body),
                API_modal
            ]
        )
    ]

exchange_dropdown = dcc.Dropdown(
    id = 'exchange',
    options=[
        {'label': 'Kraken', 'value': 'Kraken'},
        {'label': 'Coinbase', 'value': 'Coinbase'},
    ],
    multi=False,
    value='Kraken'
)

API_modal = html.Div(
    [   dbc.Modal(
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
            id="API-modal",
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
    app.logger.info(f'running load_wallet_data on {data.keys()}')
    if data is not None:
        return generate_wallet_cards(data['Wallets']['APIs'])
    else:
        raise PreventUpdate

@app.callback(
    Output("API-modal", "is_open"),
    [   Input("add-API-modal", "n_clicks"), 
        Input("API-close", "n_clicks")
    ]
)
def toggle_API_modal(n1,n2):
    ctx = dash.callback_context
    if (len(ctx.triggered)>0) & ((n1 is not None) or (n2 is not None)):
        trg = ctx.triggered[0]['prop_id'].split('.')[0]  
        if trg == "add-API-modal":
            return True
        elif trg == "API-close":
            return False
    else:
        raise PreventUpdate


@app.callback( 
    Output('api-key','invalid'), 
    Output('api-sec','invalid'),
    Output('memory', 'data'),
    Input('add-api', 'n_clicks'),
    [   State('exchange', 'value'),
        State('api-key', 'value'),
        State('api-sec', 'value'),
        State('api-pass', 'value'),
    ]
    , prevent_initial_call = True
)
def add_API(n1, exchange, api_key, api_sec, api_pass):
    ctx = dash.callback_context
    bad_api_key = False
    bad_api_sec = False 
    if (len(ctx.triggered)>0) & (n1 is not None):
        trg = ctx.triggered[0]['prop_id'].split('.')[0]  
        if api_key in [None,'']:
            bad_api_key = True
        if api_sec in [None,'']:
            bad_api_sec = True

        if bad_api_key == bad_api_sec == False:
            exch = {
                exchange : {
                    'api_key' : api_key,
                    'api_sec' : api_sec,
                    'api_pass' : api_pass,
                    'time_added': datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                }
            }
            add_to_json(type='exchange', dta=exch)
            return bad_api_key, bad_api_sec, load_settings()

        return bad_api_key, bad_api_sec, None
    else:
        raise PreventUpdate

if __name__ == '__main__':
    app.layout = layout
    app.run_server(debug=True)