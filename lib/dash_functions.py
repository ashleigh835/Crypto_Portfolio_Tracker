import os
import json

import sys
sys.path.append('../')
# from Crypto_Portfolio_Tracker.functions import generate_new_key,encrypt,decrypt,load_key

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
        'Addresses' : {}
    }
}

def clean_json(dta):
    for section in dta['Wallets'].keys():
        delete_ls = []
        for wallet_type in dta['Wallets'][section].keys():
            if dta['Wallets'][section][wallet_type] == []:
                delete_ls+=[wallet_type]     
        for wallet_type in delete_ls:
            dta['Wallets'][section].pop(wallet_type) 
    return dta

def update_settings(dta):
    app_data_loc, app_settings = locate_settings()
    dta = clean_json(dta)
    with open(app_settings, 'w') as outfile:
        json.dump(dta, outfile)

def add_to_json(type, dta):
    app_settings_dict=load_settings()

    for exch in dta.keys():
        if exch in app_settings_dict['Wallets'][type].keys():
            if app_settings_dict['Wallets'][type][exch] != []:
                app_settings_dict['Wallets'][type][exch] += [dta[exch]]
            else:
                app_settings_dict['Wallets'][type][exch] = [dta[exch]]
        else:
            app_settings_dict['Wallets'][type][exch] = [dta[exch]]
    update_settings(app_settings_dict)


def remove_entry_from_json(index,type):
    app_settings_dict=load_settings()
    dta = app_settings_dict['Wallets'][type]
    for exchange in dta.keys():
        for entry in dta[exchange]:
            if entry['id'] == index:
                app_settings_dict['Wallets'][type][exchange].remove(entry)
    update_settings(app_settings_dict)

def get_latest_index_from_json(type):
    app_settings_dict=load_settings()
    max_index =[-1]
    for wallet_type in app_settings_dict['Wallets'][type].keys():
        max_index += [ sub['id'] for sub in load_settings()['Wallets'][type][wallet_type] ]
    return max(max_index)+1