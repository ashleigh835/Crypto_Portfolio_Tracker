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

def clean_json(dta):
    delete_ls = []
    for exch in dta['Wallets']['APIs'].keys():
        if dta['Wallets']['APIs'][exch] == []:
            delete_ls+=[exch]        
    for exch in delete_ls:
        dta['Wallets']['APIs'].pop(exch)
    return dta

def update_settings(dta):
    app_data_loc, app_settings = locate_settings()
    dta = clean_json(dta)
    with open(app_settings, 'w') as outfile:
        json.dump(dta, outfile)

def add_to_json(type, dta):
    app_settings_dict=load_settings()
    if type == 'exchange':
        for exch in dta.keys():
            if exch in app_settings_dict['Wallets']['APIs'].keys():
                if app_settings_dict['Wallets']['APIs'][exch] != []:
                    app_settings_dict['Wallets']['APIs'][exch] += [dta[exch]]
                else:
                    app_settings_dict['Wallets']['APIs'][exch] = [dta[exch]]
            else:
                app_settings_dict['Wallets']['APIs'][exch] = [dta[exch]]
    update_settings(app_settings_dict)


def remove_entry_from_json(index):
    app_settings_dict=load_settings()
    dta = app_settings_dict['Wallets']['APIs']
    for exchange in dta.keys():
        for entry in dta[exchange]:
            if entry['api_id'] == index:
                dta[exchange].remove(entry)
                update_settings(app_settings_dict)
                return f"removing the API which was added on {entry['time_added']}"
    return "No entry found to be removed"

def get_latest_index_from_json():
    app_settings_dict=load_settings()
    max_index =[-1]
    for exch in app_settings_dict['Wallets']['APIs'].keys():
        max_index += [ sub['api_id'] for sub in load_settings()['Wallets']['APIs'][exch] ]
    return max(max_index)+1