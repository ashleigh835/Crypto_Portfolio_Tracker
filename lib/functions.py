from config import accepted_currencies, remap_assets, fiat_currencies

import os
import json
import pandas as pd
import numpy as np
from cryptography.fernet import Fernet

def split_pair(pair, accepted_currencies=accepted_currencies):
    """
    Take a pair and split individually based on the list of accepted currencies.
    If one asset is provided, that asset will return in a duplicated array 
    e.g.
    split_pair('VTC') return ['VTC','VTC']

    Args:
        pair (str): ASSET/ASSET string which should be split into two currencies. 
        accepted_currencies (list, optional): list of currencies which the pair can be split into. Defaults to accepted_currencies.

    Returns:
        list: list of size 2 containing each asset which the pair was split into
    """    
    default_pair = {'found':False,
             'currency_short':'',
             'currency_long':''}
    return_pair = [default_pair.copy(), default_pair.copy()]
    
    for curr in accepted_currencies:
        for curr2 in [curr,'X'+curr,'XX'+curr,'Z'+curr]:
            if (pair.startswith(curr2)) & (return_pair[0]['found'] == False):
                return_pair[0]['found'] = True
                return_pair[0]['currency_short']=curr
                return_pair[0]['currency_long']=curr2
            if (pair.endswith(curr2)) & (return_pair[1]['found'] == False):
                return_pair[1]['found'] = True
                return_pair[1]['currency_short']=curr
                return_pair[1]['currency_long']=curr2
                
    if not (return_pair[0]['found'] == return_pair[1]['found'] == True):
        if return_pair[0]['found'] == return_pair[1]['found']:
            if pair != str(np.nan):
                print(f'neither pair from {pair} were supported.')
        else:
            for i in return_pair:
                if i['found']:
                    print(f"Currency: {pair.replace(i['currency_long'],'')} not supported, consider adding to supported list")
    
    return [return_pair[0]['currency_short'],return_pair[1]['currency_short']]

def parse_pairs_from_series(df, series_name):
    """
    Adjust a dataframe - take the series and split into two columns

    Args:
        df (pandas.DataFrame): Pandas Dataframe containing the series which should be processed
        series_name (str): string representing a pandas.Series which should be processed

    Returns:
        pandas.DataFrame: adjusted dataframe and the new column names
        list: list of the series names which the series_name was parsed into
    """        
    pair_cols = ['pair_1','pair_2']
    
    pair_df = df[series_name].astype('str').apply(split_pair).apply(pd.Series)
    pair_df.columns = pair_cols
    df = df.merge(pair_df,left_index=True,right_index=True)
    
    return df, pair_cols

def remap_and_dedupe_assets(ls, remap_assets=remap_assets): 
    """
    Rename any assets in the list according to the provided dictionary

    Args:
        ls (list): list of assets which should be deduped and renamed
        remap_assets (dict, optional): dictionairy to apply the rename ruling. Defaults to remap_assets from config.py.

    Returns:
        list: unique and remapped assets
    """     
    i=0
    for asset in ls:
        if asset in remap_assets.keys():
            ls[i]=remap_assets[asset]
        i+=1
    # Loop through again after remapping to remove DUD currencies and not break indexes
    for asset in ls:
        if asset in ['',str(np.nan),np.nan]:
            ls.remove(asset)
    return list(set(ls))

def remap_series(df, series_name, remap_assets=remap_assets): 
    """
    Rename any assets in the dataframe according to theprovided dictionary

    Args:
        df (pandas.DataFrame): Pandas Dataframe containing the series which should be processed
        series_name (str): string representing a pandas.Series which should be processed
        remap_assets (dict, optional): dictionairy to apply the rename ruling. Defaults to remap_assets from config.py.

    Returns:
        pandas.DataFrame: adjusted dataframe
    """     
    for asset in remap_assets:
        df[series_name] = df[series_name].str.replace(asset,remap_assets[asset])
    return df

def kraken_aggregate_balances_per_day_trade(df, currencies, pair_cols):
    """
    create a dataframe which has a column for each asset in the currencies ls
    these columns will have the balance change for each date

    Args:
        df (pandas.DataFrame): Pandas Dataframe containing the data to be aggregated
        currencies (list): list of currencies which should be aggregated
        pair_cols (list): two items which represent columns with the same names in df:
        - The first pair column is the value for buy and sell volume
        - The second pair column is the valule for fees and cost

    Returns:
        pandas.DataFrame: aggregated data with a column for each currency listing each balance change per date
    """
    
    df['vol'] = df['vol'].astype('float')
    df['fee'] = df['fee'].astype('float')
    df['cost'] = df['cost'].astype('float')
    for currency in currencies:
        if currency not in df.columns:
            df[currency]=0

        df.loc[(df.type=='sell') & (df[pair_cols[0]]==currency), currency] = df[currency] + (df.vol*-1)
        df.loc[(df.type=='buy') & (df[pair_cols[0]]==currency), currency] = df[currency] + (df.vol)

        df.loc[df.pair_2==currency, currency] = df[currency] + (df.fee*-1)

        df.loc[(df.type=='sell') & (df[pair_cols[1]]==currency), currency] = df[currency] + (df.cost)
        df.loc[(df.type=='buy') & (df[pair_cols[1]]==currency), currency] = df[currency] + (df.cost*-1)
    
    return df.groupby('date').agg('sum')[currencies]

def kraken_aggregate_balances_per_day_ledger(df, currencies):
    """
    create a dataframe which has a column for each asset in the currencies ls
    these columns will have the balance change for each date

    Args:
        df (pandas.DataFrame): Pandas Dataframe containing the data to be aggregated
        currencies (list): list of currencies which should be aggregated

    Returns:
        pandas.DataFrame: aggregated data with a column for each currency listing each balance change per date
    """    
    df['fee'] = df['fee'].astype('float')
    for currency in currencies:
        if currency not in df.columns:
            df[currency]=0
        df.loc[df.asset==currency, currency] = df[currency] + (df['fee']*-1)
    
    df['amount'] = df['amount'].astype('float')
    for currency in list(set(fiat_currencies) & set(currencies)):
        if currency not in df.columns:
            df[currency]=0
            
        df.loc[(df.asset==currency) & (df.type=='deposit'),
               currency] = df[currency] + (df['amount'])
        df.loc[(df.asset==currency) & (df.type=='withdrawal'), 
               currency] = df[currency] + (df['amount']*-1)

    return df.groupby('date').agg('sum')[currencies]

def coinbase_aggregate_balances_per_day(df, currencies, pair_cols=['pair_1','pair_2']):
    """
    create a dataframe which has a column for each asset in the currencies ls
    these columns will have the balance change for each date

    Args:
        df (pandas.DataFrame): Pandas Dataframe containing the data to be aggregated
        currencies (list): list of currencies which should be aggregated
        pair_cols (list): two items which represent columns with the same names in df:
        - The first pair column is the value for buy and sell volume
        - The second pair column is the valule for fees and cost

    Returns:
        pandas.DataFrame: aggregated data with a column for each currency listing each balance change per date
    """    
    df['fee'] = df['fee'].fillna(0).astype('float')
    df['vol'] = df['vol'].fillna(0).astype('float')
    df['cost'] = df['cost'].fillna(0).astype('float')
    for currency in currencies:
        if currency not in df.columns:
            df[currency]=0
            
        df.loc[df.asset==currency, currency] = df[currency] + (df['fee']*-1) + df['vol']

        df.loc[(df.type=='buy') & (df[pair_cols[0]]==currency), currency] = df[currency] + (df['vol'])
        df.loc[(df.type=='buy') & (df[pair_cols[1]]==currency), currency] = df[currency] + (df['cost']*-1)
    
    return df.groupby('date').agg('sum')[currencies]

def load_key():    
    """
    Load the decryption key from environmental variables

    Returns:
        str (utf-8): encoded decryption key
    """    
    if os.getenv('KEY') == None:
        key = input("""
        Please enter password:
        """)
        os.environ['KEY'] = key

    return os.environ['KEY'].encode('utf-8')

def generate_new_key():
    """
    Generate a new decryption key

    Returns:
        str (utf-8): encoded decryption key
    """
    return Fernet.generate_key()

def encrypt(str):
    """
    encrypt string using the key in global variables (if not stored, will prompt for it)

    Args:
        str (str): string to be encrypted, must be encoded

    Returns:
        str (utf-8): encrypted string
    """
    key = load_key()
    cipher_suite = Fernet(key)
    return cipher_suite.encrypt(str)
    
def decrypt(str):
    """
    decrypt string using the key in global variables (if not stored, will prompt for it)

    Args:
        str (str): string to be decrypted, must be encoded

    Returns:
        str (utf-8): decrypted string
    """
    key = load_key()
    cipher_suite = Fernet(key)
    return cipher_suite.decrypt(str)

## SETTINGS FILE INTERACTION
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