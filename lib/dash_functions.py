import os
import json

import sys
sys.path.append('../')
from functions import generate_new_key,encrypt,decrypt,load_key

def locate_settings():    
    app_data_loc = os.getcwd()+os.sep+'data'
    app_settings = app_data_loc+os.sep+'app_data.json'
    return app_data_loc, app_settings

def load_settings():
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
    return {
    'Wallets' : {
        'APIs' : {},
        'Address' : {}
    }
}

def update_settings(dta):
    app_data_loc, app_settings = locate_settings()
    with open(app_settings, 'w') as outfile:
        json.dump(dta, outfile)

def add_to_json(type, dta):
    app_settings_dict=load_settings()
    if type == 'exchange':
        for exch in dta.keys():
            if exch in app_settings_dict['Wallets']['APIs'].keys():
                app_settings_dict['Wallets']['APIs'][exch] += [dta[exch]]
            else:
                app_settings_dict['Wallets']['APIs'][exch] = [dta[exch]]
    update_settings(app_settings_dict)
