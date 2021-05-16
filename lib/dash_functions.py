import os
import json

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html

# import sys
# sys.path.append('../')
# from Crypto_Portfolio_Tracker.functions import generate_new_key,encrypt,decrypt,load_key

def locate_settings():    
    """
    find settings file and location

    Returns:
        path (str): location where settings file is stored
        file (str): full path of settings file
    """
    app_data_loc = os.getcwd()+os.sep+'data'
    app_settings = app_data_loc+os.sep+'app_data.json'
    return app_data_loc, app_settings

def load_settings():
    """
    load the json data into memory from file
    if the set directory for the data doesn't exist it will be created
    if there's no settings file, a blank default will be created

    Returns:
        dict: contains wallet information
    """
    app_data_loc, app_settings = locate_settings()

    if os.path.exists(app_data_loc) == False:
        os.mkdir(app_data_loc)
    if os.path.isfile(app_settings) == False:
        app_settings_dict = settings_default()
    else:
        with open(app_settings) as json_file:
            app_settings_dict = json.load(json_file)
    return app_settings_dict

def settings_default():
    """
    default json data file structure

    Returns:
        dict: contains app data including wallet information
    """
    return {
    'Wallets' : {
        'APIs' : {},
        'Addresses' : {}
    }
}

def clean_json(wallet_dict):
    """
    - remove empty subtype dictionaries

    Args:
        wallet_dict (dict): dictionary of {wallet_type: {wallet_subtype:[list of wallets]}}

    Returns:
        wallet_dict (dict): cleaned dictionary of {wallet_type: {wallet_subtype:[list of wallets]}}
    """
    for wallet_type in wallet_dict['Wallets'].keys():
        delete_ls = []
        for wallet_sub_type in wallet_dict['Wallets'][wallet_type].keys():
            if wallet_dict['Wallets'][wallet_type][wallet_sub_type] == []:
                delete_ls+=[wallet_sub_type]     
        for wallet_sub_type in delete_ls:
            wallet_dict['Wallets'][wallet_type].pop(wallet_sub_type) 
    return wallet_dict

def update_settings(wallet_dict):
    """
    Overwrite the json data file with the passed dictionary

    Args:
        wallet_dict (dict): dictionary of {wallet_type: {wallet_subtype:[list of wallets]}}
    """
    app_settings_file = locate_settings()[1]
    wallet_dict = clean_json(wallet_dict)
    with open(app_settings_file, 'w') as outfile:
        json.dump(wallet_dict, outfile)

# wallet_dict (dict) = {
#     wallet_type : {
#         wallet_sub_type : wallets (list)
#     }
# }
# wallet_type = API/Address Wallet
# wallet_subtype = API Exchange/Asset Type
# wallets = API credentials/Wallet Address
def add_entry_to_json(wallet_type, wallet_subtypes):
    """
    add a wallet to the respective wallet_type + wallet_subtype - overwrites the json data file

    Args:
        wallet_type (dict): Addresses/APIs - Whether the list of contains Addresses or APIs respectively
        wallet_subtypes (dict): dictionary of {wallet_subtype:[list of wallets]}
    """
    app_settings_dict=load_settings()

    for wst in wallet_subtypes.keys():
        if wst in app_settings_dict['Wallets'][wallet_type].keys():
            if app_settings_dict['Wallets'][wallet_type][wst] != []:
                app_settings_dict['Wallets'][wallet_type][wst] += [wallet_subtypes[wst]]
            else:
                app_settings_dict['Wallets'][wallet_type][wst] = [wallet_subtypes[wst]]
        else:
            app_settings_dict['Wallets'][wallet_type][wst] = [wallet_subtypes[wst]]
    update_settings(app_settings_dict)


def remove_entry_from_json(index,wallet_type):
    """
    remove a wallet by index from the respective wallet_type + wallet_subtype - overwrites the json data file

    Args:
        index (int): the index (represented as id within the wallet dict) of the wallet
        wallet_type (str): Addresses/APIs - Whether the wallet contains an Address or API
    """
    app_settings_dict=load_settings()
    wallet_subtypes = app_settings_dict['Wallets'][wallet_type]
    for wst in wallet_subtypes.keys():
        for wallet in wallet_subtypes[wst]:
            if wallet['id'] == index:
                app_settings_dict['Wallets'][wallet_type][wst].remove(wallet)
    update_settings(app_settings_dict)

def get_latest_index_from_json(wallet_type):
    """
    provide an unused index for the given wallet_type
    indexes are not unique accross wallet_types

    Args:
        wallet_type (str): Addresses/APIs

    Returns:
        int: unique integer which can be used as an index within the given wallet_type
    """
    app_settings_dict=load_settings()
    max_index =[-1]
    for wallet_subtype in app_settings_dict['Wallets'][wallet_type].keys():
        max_index += [ wallet['id'] for wallet in load_settings()['Wallets'][wallet_type][wallet_subtype] ]
    return max(max_index)+1

def mask_str(str):
    """
    hide characters from a given string

    Args:
        str (str): string which should be masked

    Returns:
        str: masked string
    """
    if len(str)<8:
        return f"{str[0]}..."
    else:
        return f"{str[0:3]}...{str[len(str)-3:]}"


# wallet_dict (dict) = {
#     wallet_type : {
#         wallet_sub_type : wallets (list)
#     }
# }
# wallet_type = API/Address Wallet
# wallet_subtype = API Exchange/Asset Type
# wallets = API credentials/Wallet Address

## LAYOUT FUNCTIONS
# SETTINGS

def generate_individual_wallet_listgroup(wallets,wallet_type):
    """
    Generate list of the wallets for a specific wallet subtype e.g.
    - creates a list of all the sub wallets listed under Kraken exchange or
    - creates a list of all the sub wallet addresses listed under Bitcoin etc.

    Args:
        wallets (list): list of wallet Addresses/APIs dictionaries containing wallet information - each entry should have the following keys: 
        -   'time_added'
        -   either 'api_key' for APIs or 'address' for Addresses
        -   'id'

        wallet_type (str): Addresses/APIs - Whether the list of contains Addresses or APIs respectively

    Returns:
        list: list of html listgroups of the sub addresses provided 
    """
    wallet_name_dct = {'APIs' : 'api_key', 'Addresses' : 'address' }
    ls=[]
    for wallet in wallets: 
        wallet_str = [
            html.Span(f"{mask_str(wallet[wallet_name_dct[wallet_type]])}", style={'color':'CornflowerBlue'}),
            html.Span(f" added {wallet['time_added']}", style={'font-size':'smaller'} ) 
        ]
        ls+=[   
            dbc.ListGroupItem(
                [   dbc.Row(
                        [   dbc.Col(wallet_str,className="card-text"),
                        # [   dbc.Col(html.P(wallet_str,className="card-text")),
                            dbc.Col(
                                dbc.Button(children=[html.I(className="fas fa-minus-square", style={'color':'red'})], size='sm', color='link',
                                    style={'margin':'0',"padding":"0",'background-color': 'white', 'float':'right','align':'center'},
                                    id={'index':wallet['id'],'type':f'remove-{wallet_type}'}
                                ),
                                style={'padding-right':'1%'}    
                            ),
                        ]
                    )
                ]
            )
        ]
    return ls

def generate_wallet_card_body(wallet_subtypes, wallet_type):
    """
    generate list of listgroups for the wallets within all wallet subtypes e.g.
    - creates a list of all the exchange sub wallets listed under API Wallets and Address Wallets etc. 

    Args:
        wallet_subtypes (dict): dictionary of {wallet_subtype:[list of wallets]}
        wallet_type (str): Addresses/APIs - Whether the list of contains Addresses or APIs respectively

    Returns:
        list: list of html card bodies for each key in wallet_subtypes
    """    
    ls=[]
    for wallet_subtype in wallet_subtypes:
        ls+=dbc.CardBody(
            [   dbc.CardHeader(wallet_subtype,style={'background-color': 'white', 'font-weight': 'bold'}),
                dbc.ListGroup(
                    generate_individual_wallet_listgroup(wallet_subtypes[wallet_subtype], wallet_type),
                    flush=True,
                ),
            ]
        ),
    return ls

def generate_wallet_card_header(header, wallet_type):
    """
    Creates a header and Button to be used in a html card

    Args:
        header (string): Header title
        wallet_type (str): Addresses/APIs - Whether the header will house Addresses or APIs respectively (used in the id for the button)

    Returns:
        list : list of html children with a header and a button with id for the wallet_type
    """    
    return [
        header,
        dbc.Button(children=[html.I(className="fas fa-plus-square", style={'color':'green'})], id=f'add-{wallet_type}-modal', size='sm', color='link',
            style={'margin':'0',"padding":"0",'background-color': 'light', 'float':'right'}
        )
    ]

def generate_wallet_content(wallet_subtypes, wallet_type):
    """
    determine whether to produce cards or a default card when no wallets exist for the wallet_subtype

    Args:
        wallet_subtypes (dict): dictionary of {wallet_subtype:[list of wallets]}
        wallet_type (str): Addresses/APIs - Whether the list of contains Addresses or APIs respectively

    Returns:
        list: list of html children containing card bodies of wallet_subtypes
    """    
    if len(wallet_subtypes) == 0:
        return html.P(f"Looks like you haven't added any {wallet_type} yet! Click to Add", className="card-text")
    else:
        return dbc.Card(generate_wallet_card_body(wallet_subtypes,wallet_type))

def generate_modal_form_group(lbl, formId, feedback, formTxt):
    """
    use default styling to create wallet modal forms (we use this each time)

    Args:
        lbl (str): Form label for the input entry
        formId (str): id to use for the input and validation
        feedback (str): feedback to display when invalid
        formTxt (str): secondary text to display below input

    Returns:
        FormGroup: FormGroup item (dash_bootstrap_components) with a Label and input entry
    """    
    return dbc.FormGroup(
        [   dbc.Label(lbl, html_for=formId, width = 2, style={'padding':'2%'}),
            dbc.Col(
                [   dbc.Input(type="text", id=formId),
                    dbc.FormFeedback(feedback, valid=False),
                    dbc.FormText(formTxt,color="secondary")
                ],
                align = 'center'
            )
        ],
        row=True,
    )

def generate_modal_footer(formId):
    """
    use default styling to create ADD and CANCEL buttons for a modal with dynamic IDs based on input

    Args:
        formId (str): id to use for the footer buttons

    Returns:
        ModalFooter: ModalFooter item (dash_bootstrap_components) with Add and Cancel buttons
    """
    return dbc.ModalFooter(
        [   dbc.ButtonGroup(
                [   dbc.Button("Add", id=f"add-{formId.lower()}", className="ml-auto",color='success'),
                    dbc.Button("Cancel", id=f"{formId}-close", className="ml-auto")
                ],
                size="sm",
            ),
        ]
    )

def generate_wallet_cards(wallet_dict):
    """
    generates a card for each wallet_type. wallet_type cards contain a card for each wallet_subtype. Each wallet_subtype card houses a list of wallets

    Args:
        wallet_dict (dict): dictionary of {wallet_type: {wallet_subtype:[list of wallets]}}

    Returns:
        list: list of html children containing cards of wallets
    """        
    # exchange selection - hardcoded options for now
    exchange_dropdown = dcc.Dropdown(
        id = 'exchange',
        options=[
            {'label': 'Kraken', 'value': 'Kraken'},
            {'label': 'Coinbase', 'value': 'Coinbase'},
        ],
        multi=False,
        value='Kraken'
    )
    # asset selection for wallet addresses - hardcoded options for now
    asset_dropdown = dcc.Dropdown(
        id = 'asset-dd',
        options=[
            {'label': 'Doge', 'value': 'DOGE'},
            {'label': 'Bitcoin', 'value': 'BTC'},
            {'label': 'Monero', 'value': 'XMR'},
            {'label': 'Cardano', 'value': 'ADA'},
        ],
        multi=False,
        value='BTC'
    )
    wallet_type_titles = {'APIs' : "Exchange Wallets", 'Addresses': "Address Wallets"}   
    wallet_modals = {
        'Addresses' : dbc.Modal(
            [   dbc.ModalHeader("Add Addresses"),
                dbc.ModalBody(
                    [   dbc.FormGroup(asset_dropdown),
                        generate_modal_form_group("Address","wallet-address","Address required",''),
                    ]
                ),
                generate_modal_footer('Addresses'),
            ],
            id="Addresses-modal",
            size="lg",
            centered=True,
            is_open=False),
        'APIs' : dbc.Modal(
            [   dbc.ModalHeader("Add API"),
                dbc.ModalBody(
                    dbc.Form(
                        [   dbc.FormGroup(exchange_dropdown),
                            generate_modal_form_group("API Key","api-key","API Key required",''),
                            generate_modal_form_group("API Secret","api-sec","API Secret required",''),
                            generate_modal_form_group("API Passphrase","api-pass",'','Not all exchanges require an API Passphrase - leave blank if not required'),
                        ]
                    )
                ),
                generate_modal_footer('API'),
            ],
            id="APIs-modal",
            size="lg",
            centered=True,
            is_open=False
        )
    }
    
    cards = []
    for wallet_type in wallet_dict:
        main_exchange_wallet_header = generate_wallet_card_header(wallet_type_titles[wallet_type],wallet_type)
        exchange_wallet_card_body = generate_wallet_content(wallet_dict[wallet_type],wallet_type)
        cards += [
            dbc.Card(
                [   dbc.CardHeader(main_exchange_wallet_header),
                    dbc.CardBody(exchange_wallet_card_body),
                ]
            ),
            html.Div(wallet_modals[wallet_type])
        ]
    return cards