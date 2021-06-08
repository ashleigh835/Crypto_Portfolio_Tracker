from config import remap_assets, fiat_currencies

import os
import pandas as pd
import numpy as np
from cryptography.fernet import Fernet

def asset_variant(asset):
    """
    generate a list of accepted asset variants (e.g. on Kraken, BTC can be listed as XXBTC etc. and we want to treat it as BTC)

    Args:
        asset (str): trading asset 

    Returns:
        list: list of accepted asset variants
    """
    return [asset,'X'+asset,'XX'+asset,'Z'+asset]
                          
def rename_asset(old_asset, accepted_currencies, remap_assets=remap_assets): 
    """
    rename an asset based on asset variants or renaming rules in dictionary provided

    Args:
        old_asset (str): asset which should be renamed
        accepted_currencies (list): list of currencies that the asset can be renamed to 
        remap_assets (dict, optional): dictionary of assets with renaming rules e.g. {'XBT' : 'BTC'}. Defaults to remap_assets from config.py.

    Returns:
        str: renamed asset
    """    
    for asset in accepted_currencies:
        # Rename the given asset if it appears in the remapping dict
        for remap_asset in remap_assets.keys():
            if old_asset in asset_variant(remap_asset):
                old_asset = remap_assets[remap_asset]            

        # Rename the current asset from the loop if it appears in the remapping dict
        tmp_asset = asset
        if asset in remap_assets.keys():
            tmp_asset=remap_assets[asset]

        # If it appears with any of the base string prefixes, accept the original version
        if old_asset in asset_variant(tmp_asset):
            return tmp_asset
                                            
    return old_asset
    
def split_symbol(symbol, accepted_currencies):  
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
    default_symbol = {'found':False,
             'currency_short':'',
             'currency_long':''}
    return_symbol = [default_symbol.copy(), default_symbol.copy()]

    for asset in accepted_currencies:
        for asset_v in asset_variant(asset):
            if (symbol == asset_v) & (return_symbol[0]['found'] == return_symbol[1]['found'] == False):
                return_symbol[0]['found'] = True
                return_symbol[0]['currency_short']=asset
                return_symbol[0]['currency_long']=asset_v
                return_symbol[1]['found'] = True
                return_symbol[1]['currency_short']=asset
                return_symbol[1]['currency_long']=asset_v
            if (symbol.startswith(asset_v)) & (return_symbol[0]['found'] == False):
                return_symbol[0]['found'] = True
                return_symbol[0]['currency_short']=asset
                return_symbol[0]['currency_long']=asset_v
            if (symbol.endswith(asset_v)) & (return_symbol[1]['found'] == False):
                return_symbol[1]['found'] = True
                return_symbol[1]['currency_short']=asset
                return_symbol[1]['currency_long']=asset_v

    if not (return_symbol[0]['found'] == return_symbol[1]['found'] == True):
        if return_symbol[0]['found'] == return_symbol[1]['found']:
            if symbol != str(np.nan):
                print(f'neither asset from {symbol} were supported.')
        else:
            for symbol_i in return_symbol:
                if symbol_i['found']: print(f"Currency: {symbol.replace(symbol_i['currency_long'],'')} not supported, consider adding to supported list")

    return [return_symbol[0]['currency_short'],return_symbol[1]['currency_short']]

def parse_pairs_from_series(df, series_name, accepted_currencies):
    """
    Adjust a dataframe - take the series and split into two columns

    Args:
        df (pandas.DataFrame): Pandas Dataframe containing the series which should be processed
        series_name (str): string representing a pandas.Series which should be processed
        accepted_currencies (list): list of currencies which the pair can be split into.

    Returns:
        pandas.DataFrame: adjusted dataframe and the new column names
        list: list of the series names which the series_name was parsed into
    """        
    pair_cols = ['pair_1','pair_2']
    pair_df = df[series_name].astype('str').apply(split_symbol, args=[accepted_currencies]).apply(pd.Series)
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

def encrypt(str, key = ''):
    """
    encrypt string using the key in global variables (if not stored, will prompt for it)

    Args:
        str (str): string to be encrypted, must be encoded

    Returns:
        str (utf-8): encrypted string
    """
    if key == '':
        key = load_key()
    cipher_suite = Fernet(key)
    return cipher_suite.encrypt(str)
    
def decrypt(str, key = ''):
    """
    decrypt string using the key in global variables (if not stored, will prompt for it)

    Args:
        str (str): string to be decrypted, must be encoded

    Returns:
        str (utf-8): decrypted string
    """
    if key == '':
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

def clean_json(app_settings_dict):
    """
    - remove empty subtype dictionaries

    Args:
        app_settings_dict (dict): dictionary of {Wallets: {wallet_type: {wallet_subtype:[list of wallets]}}}

    Returns:
        app_settings_dict (dict): cleaned dictionary of {Wallets: {wallet_type: {wallet_subtype:[list of wallets]}}}
    """
    for wallet_type in app_settings_dict['Wallets'].keys():
        delete_ls = []
        for wallet_sub_type in app_settings_dict['Wallets'][wallet_type].keys():
            if app_settings_dict['Wallets'][wallet_type][wallet_sub_type] == []:
                delete_ls+=[wallet_sub_type]     
        for wallet_sub_type in delete_ls:
            app_settings_dict['Wallets'][wallet_type].pop(wallet_sub_type) 
    return app_settings_dict

# wallet_dict (dict) = {
#     wallet_type : {
#         wallet_sub_type : wallets (list)
#     }
# }
# wallet_type = API/Address Wallet
# wallet_subtype = API Exchange/Asset Type
# wallets = API credentials/Wallet Address
# app_settings_dict = {Wallets: {wallet_type: {wallet_subtype:[list of wallets]}}}

def add_entry_to_json(wallet_type, wallet_subtypes, app_settings_dict):
    """
    add a wallet to the respective wallet_type + wallet_subtype - overwrites the json data file

    Args:
        wallet_type (dict): Addresses/APIs - Whether the list of contains Addresses or APIs respectively
        wallet_subtypes (dict): dictionary of {wallet_subtype:[list of wallets]}
        app_settings_dict (dict): dictionary of {Wallets: {wallet_type: {wallet_subtype:[list of wallets]}}}
    
    Returns:
        dictionary: clean updated dictionary of {Wallets: {wallet_type: {wallet_subtype:[list of wallets]}}}
    """
    for wst in wallet_subtypes.keys():
        if wst in app_settings_dict['Wallets'][wallet_type].keys():
            if app_settings_dict['Wallets'][wallet_type][wst] != []:
                app_settings_dict['Wallets'][wallet_type][wst] += [wallet_subtypes[wst]]
            else:
                app_settings_dict['Wallets'][wallet_type][wst] = [wallet_subtypes[wst]]
        else:
            app_settings_dict['Wallets'][wallet_type][wst] = [wallet_subtypes[wst]]

    return clean_json(app_settings_dict)


def remove_entry_from_json(index,wallet_type,app_settings_dict):
    """
    remove a wallet by index from the respective wallet_type + wallet_subtype - overwrites the json data file

    Args:
        index (int): the index (represented as id within the wallet dict) of the wallet
        wallet_type (str): Addresses/APIs - Whether the wallet contains an Address or API
        app_settings_dict (dict): dictionary of {Wallets: {wallet_type: {wallet_subtype:[list of wallets]}}}
    
    Returns:
        dictionary: clean updated dictionary of {Wallets: {wallet_type: {wallet_subtype:[list of wallets]}}}
    """
    wallet_subtypes = app_settings_dict['Wallets'][wallet_type]
    for wst in wallet_subtypes.keys():
        for wallet in wallet_subtypes[wst]:
            if wallet['id'] == index:
                app_settings_dict['Wallets'][wallet_type][wst].remove(wallet)
                
    return clean_json(app_settings_dict)

def get_latest_index_from_json(wallet_type,app_settings_dict):
    """
    provide an unused index for the given wallet_type
    indexes are not unique accross wallet_types

    Args:
        wallet_type (str): Addresses/APIs
        app_settings_dict (dict): dictionary of {Wallets: {wallet_type: {wallet_subtype:[list of wallets]}}}

    Returns:
        int: unique integer which can be used as an index within the given wallet_type
    """
    max_index =[-1]
    for wallet_subtype in app_settings_dict['Wallets'][wallet_type].keys():
        max_index += [ wallet['id'] for wallet in app_settings_dict['Wallets'][wallet_type][wallet_subtype] ]
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

def balances_from_dict(wallet_dict, key=''): 
    """
    Gather Balances from provided wallets into a dataframe

    Args:
        wallet_dict (dict): dictionary of {wallet_type: {wallet_subtype:[list of wallets]}}
        key (str, optional): decryption key

    Returns:
        pandas.DataFrame: DataFrame with indexed assets and a column for each source with the corresponding balances as values
    """
    from lib.kraken import Kraken
    from lib.coinbase import Coinbase  
    from lib.bittrex import Bittrex
    from lib.API_functions import blockchain_address_api, infura_eth_address, coinexplorer_addresses_api
    balance_functions = {'kraken':Kraken,'coinbase':Coinbase,'bittrex':Bittrex,'BTC':blockchain_address_api,'ETH':infura_eth_address, 'VTC':coinexplorer_addresses_api}
    api_df = pd.DataFrame()
    address_df = pd.DataFrame()
    full_df = pd.DataFrame()
    i={}
    for wallet_type in wallet_dict:
        for wallet_subtype in wallet_dict[wallet_type]:
            i[wallet_subtype]=0     
            if (wallet_subtype.lower() in balance_functions.keys()) and (wallet_type =='APIs'):
                for wallet in wallet_dict[wallet_type][wallet_subtype]:                    
                    exchange_class = balance_functions[wallet_subtype.lower()]
                    
                    exchange = exchange_class(wallet['api_key'].encode(), wallet['api_sec'].encode(), key)
                    balances = exchange.getBalances_Universal()
                    df = pd.DataFrame()

                    for bal in balances:
                        if len(wallet_dict[wallet_type][wallet_subtype])>1:
                            index_str = f"{wallet_subtype}_{i[wallet_subtype]}"
                        else:
                            index_str = wallet_subtype
                        tmp_df = pd.DataFrame({index_str : balances[bal]},index=[rename_asset(bal,exchange.getValidAssets_Universal())])
                        df = pd.concat([df,tmp_df], axis=0, sort=True)
                    api_df = pd.concat([api_df,df], axis=1, sort=True)
                    i[wallet_subtype]+=1


            elif (wallet_subtype.upper() in balance_functions.keys()) and (wallet_type !='APIs'):
                address_ls = [decrypt(i['address'].encode(),key).decode() for i in wallet_dict[wallet_type][wallet_subtype]]
                    
                balance_function = balance_functions[wallet_subtype]
                if wallet_subtype == 'VTC':
                    balances = balance_function(wallet_subtype,address_ls)
                else:
                    balances = balance_function(address_ls)
                if balances is not None:
                    for address in balances:
                        if len(wallet_dict[wallet_type][wallet_subtype])>1:
                            index_str = f"{wallet_subtype}_{i[wallet_subtype]}"
                        else:
                            index_str = wallet_subtype

                        balance = balances[address]['final_balance']
                        if wallet_subtype=='BTC':
                            balance = balance/100000000
                        tmp_df = pd.DataFrame({index_str : balance },index=[wallet_subtype])
                        address_df = pd.concat([address_df,tmp_df], axis=1, sort=True)
                        i[wallet_subtype]+=1

            full_df = pd.concat([api_df,address_df], axis=1, sort=True)
    full_df = add_columns_by_index(full_df.copy().fillna(0))
    return full_df

def pull_spot_prices_from_all_sources(symbols, wallet_dict, native='USD', spot_df=pd.DataFrame()):
    """
    use all exchanges to pull prices for the symbols provided

    Args:
        symbols ([str]): list of symbols to pull prices for e.g. ['BTC/USD', 'ETH/USD']
        wallet_dict (dict): dictionary of {wallet_type: {wallet_subtype:[list of wallets]}}
        native (str, optional): native currency to use as the right pairing of the spot price. Defaults to 'USD'.
        spot_df (pandas.DataFrame, optional): dataframe which spot prices will be appended to. Defaults to pd.DataFrame().

    Returns:
        pandas.DataFrame: updated dataframe with the prices for the symbols appended 
    """
    from lib.coingecko import CoinGecko    
    from lib.bittrex import Bittrex
    from lib.kraken import Kraken
    from lib.coinbase import Coinbase  

    from datetime import datetime
    exchange_classes = {'kraken':Kraken,'coinbase':Coinbase,'bittrex':Bittrex,'coingecko':CoinGecko}

    for wallet_subtype in ['coingecko'] + list(wallet_dict['Wallets']['APIs'].keys()):
        if wallet_subtype.lower() in ['coingecko','coinbase']:
            if wallet_subtype.lower() in ['coingecko']:        
                price_symbols = [bal for bal in symbols if f'{bal}/{native}' not in spot_df.columns]
                exchange_class = exchange_classes[wallet_subtype.lower()]()
                spot_price_function = exchange_class.getSymbolPrices
                valid_symbols = list(set(set(exchange_class.getValidAssets_Universal()) & set(price_symbols)))
            elif wallet_subtype.lower() in ['coinbase']:                    
                price_symbols = [f'{bal}/{native}' for bal in symbols if f'{bal}/{native}' not in spot_df.columns]
                exchange_class = exchange_classes[wallet_subtype.lower()]('', '')
                spot_price_function = exchange_class.getSpotPrices
                valid_symbols = list(set(set(exchange_class.getValidSymbols_Universal()) & set(price_symbols)))

            if len(price_symbols)>0:
                print(f"pulling prices for {price_symbols} from {wallet_subtype.lower()}")
                staked_assets = [asset for asset in price_symbols if asset.split('/')[0].endswith('.S')]
                for staked_asset in staked_assets:
                    price_symbols.remove(staked_asset)
                price_symbols += [asset.replace('.S','') for asset in staked_assets]

                valid_symbols = list(set(valid_symbols) & set(price_symbols))

                print(f"valid for {wallet_subtype}: {valid_symbols}")
                prices = spot_price_function(valid_symbols)
                prices_df = pd.DataFrame(prices, index=[datetime.now().date()])                
                for staked_asset in staked_assets:
                    non_staked_asset = staked_asset.replace('.S','')
                    if (f"{staked_asset}/{native}" not in prices_df.columns) and (f"{non_staked_asset}/{native}" in prices_df.columns) and (non_staked_asset != staked_asset):
                        prices_df[f"{staked_asset}/{native}"] = prices_df[[f"{non_staked_asset}/{native}"]].copy()  


                cols_to_append = list(prices_df.columns[~prices_df.columns.isin(list(spot_df.columns))])
                spot_df = pd.concat([spot_df,prices_df[cols_to_append]],axis=1, sort=True, join='outer')               

    return spot_df

def add_columns_by_index(df,new_col_name='Total'):
    """
    Combine columns in a dataframe into one Total column

    Args:
        df (pandas.DataFrame): dataframe containing date to be totalled
        new_col_name (str): name which will be applied to the new column

    Returns:
        pandas.DataFrame: DataFrame with appended Total column
    """
    columns_to_add = df.columns
    df[new_col_name]=0
    for col in columns_to_add:
        df[new_col_name]+=df[col].fillna(0).astype('float')
        
    # Remove anything with total = 0
    for index in df[df[new_col_name]==0].index.values:
        df = df.drop(index)
        
    return df