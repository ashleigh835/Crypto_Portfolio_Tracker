from app import app
from apps import dashboard as db , settings as ls

from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html


# Naviagation Bar Drop Down Menu - navigate to Dashboard or Settings pages
nav_drop_down = dbc.DropdownMenu(
    [   dbc.DropdownMenuItem("Dashboard", href="/Dashboard"),
        dbc.DropdownMenuItem(divider=True),
        dbc.DropdownMenuItem("Settings", href="/Settings"),
    ],
    label="Menu",
    className="ml-auto flex-nowrap mt-3 mt-md-0",
    id="menu_drop_down"
)


# Naviagation Bar layout - conists of the icon, Title and dropdown menu
navbar = dbc.Navbar(
    [   html.Div(
            dbc.Row(
                [   dbc.Col(html.Img(src=app.get_asset_url('cryptocurrency.png'), height='50px')),
                    dbc.Col(dbc.NavbarBrand("Portfolio Tracker",className="ml-2",style = {'font-size': 30, 'padding-left':'3%'})),
                ],
                no_gutters = True
            ),
        ),
        dbc.Collapse(nav_drop_down, id="navbar-collapse", navbar=True),
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
    

@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
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

if __name__ == '__main__':
    app.run_server(debug=True)
