from app import app
from apps import dashboard as db , settings as ls

from lib.functions import generate_new_key

import dash
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html

from dash.exceptions import PreventUpdate

# Navigation Bar Drop Down Menu - navigate to Dashboard or Settings pages
nav_drop_down = dbc.DropdownMenu(
    [   dbc.DropdownMenuItem("Dashboard", href="/Dashboard"),
        dbc.DropdownMenuItem(divider=True),
        dbc.DropdownMenuItem("Settings", href="/Settings"),
    ],
    label="Menu",
    className="ml-auto flex-nowrap mt-3 mt-md-0",
    id="menu_drop_down",
)

# Navigation encryption tool
nav_encrypt = dbc.Button('Encrypt', id = 'encrypt-nav', className="mt-md-0", style={'position':'fixed', 'right':'6%','width':'100px'})

# Encryption modal
encrypt_text = """If you have not yet generated an encryption key, please use the button below.
This key must match the active key when you added any wallet addresses/APIs to your account"""
encrypt_modal = dbc.Modal(
    [   dbc.ModalHeader("Encryption Key"),
        dbc.FormGroup(
            [   dbc.Input(type="text", id='encrypt-input'),
                dbc.FormFeedback('must be a valid Fernet key.', valid=False),
                dbc.FormText(encrypt_text,color="secondary")
            ],
            style={ 'padding':'2%'}
        ),
        dbc.ModalFooter(
            [   dbc.Button('Generate New Key', id='encrypt-gen', color='warning',size="sm"),
                dbc.ButtonGroup(
                    [   dbc.Button("Submit Key", id=f'encrypt-submit', className="ml-auto",color='success'),
                        dbc.Button("Cancel", id='encrypt-close', className="ml-auto")
                    ],
                    size="sm",
                ),
            ]
        ),
    ],
    id="encrypt-modal",
    size="md",
    centered=True,
    is_open=False,
)
# Temporary button to check the current encryption Key
navtest=dbc.Button('test-key', id = 'encrypt-test', className="mt-md-0")
# Navigation Bar layout - conists of the icon, Title and dropdown menu
navbar = dbc.Navbar(
    [   dcc.Store(id='encryption-key', storage_type='memory'),
        dcc.Store(id='encryption-key-set', storage_type='memory', data=False),
        html.Div(
            dbc.Row(
                [   dbc.Col(html.Img(src=app.get_asset_url('cryptocurrency.png'), height='50px')),
                    dbc.Col(dbc.NavbarBrand("Portfolio Tracker",className="ml-2",style = {'font-size': 30, 'padding-left':'3%'})),
                ],
                no_gutters = True
            ),
        ),
        dbc.Collapse([navtest,nav_encrypt, nav_drop_down, encrypt_modal], id="navbar-collapse", navbar=True),

    ],
    color='dark',
    dark=True,
    fixed='top'
)

# Project Footer
footer = html.Footer(
    [   """This project is licensed under the terms of the GNU AFFERO GENERAL PUBLIC LICENSE (V3).""",                
        dcc.Markdown("""Icons made by [Eucalyp](https://www.flaticon.com/authors/eucalyp) from [Flaticon](https://www.flaticon.com/)""")
    ],
    style = {'font-size': 10}
)

def default_layout(content):
    """
    Returns content in the default page structure. All pages will be rendered through this default layout.
    i.e. all pages will have the Navigation header and project footer

    Args:
        content (html): page data to render

    Returns:
        html: content wrapped in a default layout
    """    
    return html.Div(
        children=[
            dcc.Location(id='url', refresh=False),

            dbc.Row(
                [dbc.Col(navbar)],
                align='center'
            ),


            html.Div(
                content,
                id='page-content',
                style={'padding-top':'70px'}
            ),

            html.Div(
                footer,
                style={
                    "position": "fixed",
                    "bottom": 0,
                    "left": 0,
                    "right": 0,
                    'padding-left':'1%',
                    'padding-right':'1%'
                }        
            )
        ]
    )

# Render page through the default project layout. Initializes with the Dashboard layout
app.layout = default_layout(db.layout)
    

@app.callback(Output('page-content', 'children'),[Input('url', 'pathname')])
def display_page(pathname):
    """
    Change in url will result in this callback.
    Changes the page content based on the url change

    Args:
        pathname (str): url of page

    Returns:
        html: returns page based on provided url
    """    
    if pathname == '/Dashboard':
        return db.layout
    elif pathname == '/Settings':
        return ls.layout
    else:
        return html.Div(pathname)

@app.callback(
    Output('encryption-key','data'),Output('encryption-key-set','data'),Output('encrypt-input','invalid'),
    Input('encrypt-submit','n_clicks'),Input('encrypt-gen','n_clicks'),
    State('encrypt-input','value'),State('encryption-key','data'),
    prevent_initial_call = True
)
def store_encryption(n1,n2,key_input,stored_key):
    """
    [summary]

    Args:
        n1 (n_clicks): number of times 'encrypt-submit' has been clicked (Submit Key button within the encrypt modal)
        n2 (n_clicks): number of times 'encrypt-gen' has been clicked (Generate New Key button within the encrypt modal)
        key_input (str): encryption string from input box
        stored_key (str): encryption key currently stored in the dcc.Store method

    Raises:
        PreventUpdate: error handling, if neither the generate or submit buttons were pressed, break function

    Returns:
        str: encryption key 
        bool: whether the key has been set or not, stored in the dcc.Store method
        bool: validity of the key string in the input box
    """
    ctx = dash.callback_context
    if (len(ctx.triggered)>0) & ([n1,n2] != [None]*2):
        trg = ctx.triggered[0]['prop_id'].split('.')[0]  
        if trg == "encrypt-gen":
            key = generate_new_key().decode()
        elif trg == 'encrypt-submit':
            if key_input in [None,'']:
                return stored_key,False,True
            key = key_input   
        else:            
            app.logger.info(f'error! encryption triggered by: {trg}')
            raise PreventUpdate
        return key,True,False

    else:
        raise PreventUpdate

@app.callback(
    Output("encrypt-modal", "is_open"),Output('encrypt-nav', 'children'),Output('encrypt-nav', 'outline'),Output('encrypt-nav', 'disabled'),
    Input('encrypt-nav','n_clicks'),Input("encrypt-close", "n_clicks"),Input("add-Addresses-modal", "n_clicks"),Input("add-APIs-modal",'n_clicks'),Input('encryption-key-set','data'),
    State('encrypt-nav', 'children'),State('encrypt-nav', 'outline'),State('encrypt-nav', 'disabled'),
    prevent_initial_call = True
)
def encryption_set(n1,n2,n3,n4,key_set,btn_text,outline,disabled):
    """
    [summary]

    Args:
        n1 (n_clicks): number of times 'encrypt-nav' has been clicked 
        n2 (n_clicks): number of times 'encrypt-close' has been clicked (close within the encrypt modal)
        n3 (n_clicks): number of times 'add-Addresses-modal' has been clicked
        n4 (n_clicks): number of times 'encryption-key-set' has been clicked
        key_set (bool): whether the key has been set or not, stored in the dcc.Store method
        btn_text (str): string displayed for the encrypt-nav button
        outline (bool): whether the outline style is applied to the encrypt-nav button
        disabled (bool): whether the encrypt-nav button is disabled 

    Raises:
        PreventUpdate: error handling, if non-expected buttons were pressed, break function. Also no update if the key was not set 

    Returns:
        bool: whether the encrypt modal should be open
        str: string displayed for the encrypt-nav button
        bool: whether the outline style is applied to the encrypt-nav button
        bool: whether the encrypt-nav button is disabled 
    """
    ctx = dash.callback_context
    trg = ctx.triggered[0]['prop_id'].split('.')[0]  
    if (len(ctx.triggered)>0) & ([n1,n2,n3,n4] != [None]*4):
        if (trg in ["encrypt-nav",'add-Addresses-modal','add-APIs-modal']) & (key_set == False):
            return True,btn_text,outline,disabled
        elif trg == "encrypt-close":
            return False,btn_text,outline,disabled
        elif trg == 'encryption-key-set':
            if key_set == True:
                return False, 'Encrypted', True, True
    raise PreventUpdate

@app.callback(Output('encrypt-test','children'),Input('encrypt-test','n_clicks'),State('encryption-key','data'),prevent_initial_call = True)
def test(n1,dta):
    ctx = dash.callback_context
    if (len(ctx.triggered)>0) & (n1 is not None):
        if dta not in ['',None]:
            return dta
    return 'test-key'

if __name__ == '__main__':
    app.run_server(debug=True)
