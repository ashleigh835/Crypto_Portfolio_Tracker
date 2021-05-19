import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html

from lib.functions import mask_str, decrypt

def generate_individual_wallet_listgroup(wallets,wallet_type,key=''):
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
        key (str, optional): decryption key

    Returns:
        list: list of html listgroups of the sub addresses provided 
    """
    wallet_name_dct = {'APIs' : 'api_key', 'Addresses' : 'address' }
    ls=[]
    for wallet in wallets: 
        if key == '':
            wallet_str = [
                html.Span(f"Added {wallet['time_added']}", style={'font-size':'smaller'} ),
                html.Span(f" unusable until decryption key entered", style={'font-size':'smaller', 'font-style': 'italic', 'color' : 'LightCoral'} ) 
            ]
        else:
            wallet_str = [
                html.Span(f"{mask_str(decrypt(wallet[wallet_name_dct[wallet_type]].encode(), key).decode())}", style={'color':'CornflowerBlue'}),
                html.Span(f" added {wallet['time_added']}", style={'font-size':'smaller'} ) 
            ]
        ls+=[   
            dbc.ListGroupItem(
                [   dbc.Row(
                        [   dbc.Col(wallet_str,className="card-text"),
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

def generate_wallet_card_body(wallet_subtypes, wallet_type, key=''):
    """
    generate list of listgroups for the wallets within all wallet subtypes e.g.
    - creates a list of all the exchange sub wallets listed under API Wallets and Address Wallets etc. 

    Args:
        wallet_subtypes (dict): dictionary of {wallet_subtype:[list of wallets]}
        wallet_type (str): Addresses/APIs - Whether the list of contains Addresses or APIs respectively
        key (str, optional): decryption key

    Returns:
        list: list of html card bodies for each key in wallet_subtypes
    """    
    ls=[]
    for wallet_subtype in wallet_subtypes:
        ls+=dbc.CardBody(
            [   dbc.CardHeader(wallet_subtype,style={'background-color': 'white', 'font-weight': 'bold'}),
                dbc.ListGroup(
                    generate_individual_wallet_listgroup(wallet_subtypes[wallet_subtype], wallet_type, key),
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

def generate_wallet_content(wallet_subtypes, wallet_type, key=''):
    """
    determine whether to produce cards or a default card when no wallets exist for the wallet_subtype

    Args:
        wallet_subtypes (dict): dictionary of {wallet_subtype:[list of wallets]}
        wallet_type (str): Addresses/APIs - Whether the list of contains Addresses or APIs respectively
        key (str, optional): decryption key

    Returns:
        list: list of html children containing card bodies of wallet_subtypes
    """    
    if len(wallet_subtypes) == 0:
        return html.P(f"Looks like you haven't added any {wallet_type} yet! Click to Add", className="card-text")
    else:
        return dbc.Card(generate_wallet_card_body(wallet_subtypes,wallet_type,key))

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
                [   dbc.Input(type="text", id=formId, autoComplete=False),
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

def generate_wallet_cards(wallet_dict, key=''):
    """
    generates a card for each wallet_type. wallet_type cards contain a card for each wallet_subtype. Each wallet_subtype card houses a list of wallets

    Args:
        wallet_dict (dict): dictionary of {wallet_type: {wallet_subtype:[list of wallets]}}
        key (str, optional): decryption key

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
        exchange_wallet_card_body = generate_wallet_content(wallet_dict[wallet_type],wallet_type, key)
        cards += [
            dbc.Card(
                [   dbc.CardHeader(main_exchange_wallet_header),
                    dbc.CardBody(exchange_wallet_card_body),
                ]
            ),
            html.Div(wallet_modals[wallet_type])
        ]
    return cards

def generate_balance_table(df, prices_df):
    """
    generates a table from balance dataframe including price data

    Args:
        df (pandas.DataFrame): DataFrame where index represents the asset with a column for each balance source and a Total column
        prices_df (pandas.DataFrame): DataFrame with daily prices per pairs

    Returns:
        Table (dash_bootsrap_components): HTML table with data from provided table
    """     
    wallet_str = []  
    for asset, balances in df.iterrows():
        cols_ls = [html.Td(asset)]
        for column in df.columns:
            if balances[column] not in ['',0]:   
                if asset == 'USD':
                    cols_ls+=[html.Td(html.Span(f"${float(balances[column]):,.2f}", style={'color':'green', 'font-weight': 'bold'}))]
                else:                    
                    cols_ls+=[
                        html.Td([
                            f"{float(balances[column]):,.5f}",
                            html.Span(
                                f" ${float(balances[column]) * prices_df[f'{asset}/USD'].tail(1).iloc[0]:,.2f}", style={'color':'green', 'font-weight': 'bold'}
                            )
                        ])
                    ]
            else:
                cols_ls+=[html.Td('')]
            
        wallet_str += [ html.Tr(cols_ls) ] 
    table = [
        html.Thead(
            html.Tr([html.Th('')]+[html.Th(col) for col in df.columns])
        ),
        html.Tbody(wallet_str)
    ]
    return dbc.Table(table, striped=True, bordered=False, hover=True, style={'text-align':'center'})