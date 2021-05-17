from app import app
from lib.dash_functions import generate_wallet_cards
from lib.functions import load_settings, add_entry_to_json, remove_entry_from_json, get_latest_index_from_json

import json
from datetime import datetime

import dash_core_components as dcc
import dash_html_components as html
import dash
from dash.dependencies import Input, Output, State, ALL
from dash.exceptions import PreventUpdate

# default style for the tab & selected tab
tab_Style = {
    'padding': '0',
    'height': '44px',
    'line-height': '44px'
}

layout = html.Div(
    [   dcc.Store(data=load_settings(), id='memory', storage_type='session'), #, clear_data =True),
        dcc.Tabs(
            id='settings-tab', 
            value='Wallet', 
            children=[
                dcc.Tab(label='Wallet Settings', value='Wallet',style=tab_Style,selected_style=tab_Style),
                dcc.Tab(label='User Settings', value='User',style=tab_Style,selected_style=tab_Style),
            ],
        ),
        html.Hr(),
        html.Div(id='settings-tab-content-settings'),
    ]
)

wallet_content = html.Div(id='wallet')
user_content = html.Div("COMING SOON!", id='user')

@app.callback(Output('settings-tab-content-settings', 'children'),Input('settings-tab', 'value'))
def render_tab_content(tab):
    """
    Render tab content based on the selected tab

    Args:
        tab (str): string value associated with the id: db-tab

    Returns:
        html: html content based on tab selected
    """    
    app.logger.info(f'running render_tab_content on {tab}')
    if tab == 'Wallet':
        return wallet_content
    if tab == 'User':
        return user_content

@app.callback(Output('wallet', 'children'),Input('memory', 'data'))
def load_wallet_data(data):
    """
    trigger when the stored data for id 'memory' changes and updates the children of the tab_content

    Args:
        data (dict): stored in the id 'memory'

    Raises:
        PreventUpdate: doesn't update if data is empty

    Returns:
        list: list of html children containing cards of wallets
    """
    if data is not None:
        app.logger.info(f'running load_wallet_data on {data.keys()}')
        return generate_wallet_cards(data['Wallets'])
    else:
        raise PreventUpdate

@app.callback(Output("APIs-modal", "is_open"),Input("add-APIs-modal", "n_clicks"), Input("API-close", "n_clicks"),State('encryption-key-set','data'))
def toggle_API_modal(n1,n2,key_set):
    """
    Show or hide the modal based on which button was clicked

    Args:
        n1 (n_clicks): number of times 'add-APIs-modal' has been clicked
        n2 (n_clicks): number of times 'API-close' has been clicked
        key_set (bool): whether the key has been set or not, stored in the dcc.Store method

    Raises:
        PreventUpdate: doesn't update if the trigger didn't come from a click

    Returns:
        bool: True or False on whether to show or hide the modal
    """
    ctx = dash.callback_context
    if (len(ctx.triggered)>0) & ([n1,n2] != [None]*2):
        if key_set == True:
            trg = ctx.triggered[0]['prop_id'].split('.')[0]  
            if trg == "add-APIs-modal":
                return True
            elif trg == "API-close":
                return False
    raise PreventUpdate

@app.callback(Output("Addresses-modal", "is_open"),Input("add-Addresses-modal", "n_clicks"), Input("Addresses-close", "n_clicks"),State('encryption-key-set','data'))
def toggle_Addresses_modal(n1,n2,key_set):
    """
    Show or hide the modal based on which button was clicked

    Args:
        n1 (n_clicks): number of times 'add-Addresses-modal' has been clicked
        n2 (n_clicks): number of times 'Addresses-close' has been clicked
        key_set (bool): whether the key has been set or not, stored in the dcc.Store method

    Raises:
        PreventUpdate: doesn't update if the trigger didn't come from a click

    Returns:
        bool: True or False on whether to show or hide the modal
    """
    ctx = dash.callback_context
    if (len(ctx.triggered)>0) & ([n1,n2] != [None]*2):
        if key_set == True:
            trg = ctx.triggered[0]['prop_id'].split('.')[0]  
            if trg == "add-Addresses-modal":
                return True
            elif trg == "Addresses-close":
                return False
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
        State('api-key','invalid'), 
        State('api-sec','invalid'),
        State('asset-dd', 'value'),
        State('wallet-address', 'value'),
        State('wallet-address','invalid'), 
        State('encryption-key','data'),
    ]
    , prevent_initial_call = True
)
def add_or_remove_wallet(n1, n2, n3, n4, exchange, api_key, api_sec, api_pass, bad_api_key, bad_api_sec, asset, address, bad_address, stored_key):
    """
    Add/remove a wallet to/from the json data file

    Args:
        n1 (n_clicks): number of times 'add-api' has been clicked (add button within the api modal)
        n2 (n_clicks): number of times 'add-addresses' has been clicked (add button within the address modal)
        n3 ([n_clicks]): list number of times any of the 'remove-APIs' buttons have been clicked (list item for each index)
        n4 ([n_clicks]): list number of times any of the 'add-api' buttons have been clicked (list item for each index)
        exchange (str): exchange selected in the dropdown of the api modal
        api_key (str): api key entered in the input box of the api modal
        api_sec (str): api secret entered in the input box of the api modal
        api_pass (str): api passphrase entered in the input box of the api modal
        bad_api_key (bool): current validity status of the api_key input
        bad_api_sec (bool): current validity status of the api_sec input
        asset (str): asset selected in the dropdown of the address modal
        address (str): address entered in the input box of the address modal
        bad_address (bool): current validity status of the address input
        stored_key (str): stored decryption key

    Raises:
        PreventUpdate: doesn't add/remove if the trigger didn't come from a click or the address/API details were invalid

    Returns:
        bool: wallet address string validity
        bool: api key string validity
        bool: api secret string validity
        dict: freshly reloaded json data dict from file after adding/removing info
    """
    ctx = dash.callback_context
    if (len(ctx.triggered)>0) & (([n1,n2]+n3+n4) != ([None]*(2+len(n3)+len(n4)))):
        trg = ctx.triggered[0]['prop_id'].split('.')[0]
        if trg == 'add-api':
            bad_api_key = False
            bad_api_sec = False 
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
                add_entry_to_json('APIs', exch)
                return bad_address, bad_api_key, bad_api_sec, load_settings()

            return False, bad_api_key, bad_api_sec, None
        elif trg == 'add-addresses':
            bad_address = False
            if address in [None,'']:
                return True, bad_api_key, bad_api_sec, None
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
                add_entry_to_json('Addresses', addr)
                return False, bad_api_key, bad_api_sec, load_settings()  

        else:
            trg_dta = json.loads(trg)
            app.logger.info(remove_entry_from_json(trg_dta['index'],trg_dta['type'].split('-')[1]))
            return bad_address, bad_api_key, bad_api_sec, load_settings()
    else:
        raise PreventUpdate

if __name__ == '__main__':
    import sys
    sys.path.append('../')

    app.layout = layout
    app.run_server(debug=True)