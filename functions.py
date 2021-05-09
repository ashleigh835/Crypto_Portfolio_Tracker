from packages import *
from config import *

def split_pair(pair, accepted_currencies=accepted_currencies):
    """
    Take a pair and split individually based on the list of accepted currencies.
    If one asset is provided, that asset will return in a duplicated array 
    e.g.
    split_pair('VTC') return ['VTC','VTC']
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
    Returns the adjusted dataframe and the new column names
    """
    pair_cols = ['pair_1','pair_2']
    
    pair_df = df[series_name].astype('str').apply(split_pair).apply(pd.Series)
    pair_df.columns = pair_cols
    df = df.merge(pair_df,left_index=True,right_index=True)
    
    return df, pair_cols

def remap_and_dedupe_assets(ls, remap_assets=remap_assets):  
    """
    Rename any assets in the list according to the default 'remap_assets' dict in the config
    Returns a list of unique assets
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
    Rename any assets in the dataframe according to the default 'remap_assets' dict in the config
    Returns the adjusted dataframe
    """ 
    for asset in remap_assets:
        df[series_name] = df[series_name].str.replace(asset,remap_assets[asset])
    return df

def aggregate_balances_per_day_trade(df, currencies, pair_cols):
    """
    Return a dataframe which has a column for each asset in the currencies ls
    these columns will have the balance change for each date
    Works off the assumption that there are two columns (pair_cols)
        The first pair column is the valule for buy and sell volume
        The second pair column is the valule for fees and cost
        (THIS IS HOW IT'S SET TO BE IN KRAKEN)
    """
    
    df['vol'] = df['vol'].astype('float')
    df['fee'] = df['fee'].astype('float')
    df['cost'] = df['cost'].astype('float')
    for currency in currencies:
        df[currency]=0

        df.loc[(df.type=='sell') & (df[pair_cols[0]]==currency),
               currency] = df[currency] + (df.vol*-1)
        df.loc[(df.type=='buy') & (df[pair_cols[0]]==currency), 
               currency] = df[currency] + (df.vol)

        df.loc[df.pair_2==currency, currency] = df[currency] + (df.fee*-1)

        df.loc[(df.type=='sell') & (df[pair_cols[1]]==currency)
               , currency] = df[currency] + (df.cost)
        df.loc[(df.type=='buy') & (df[pair_cols[1]]==currency)
               , currency] = df[currency] + (df.cost*-1)
    
    return df.groupby('date').agg('sum')[currencies]

def aggregate_balances_per_day_ledger(df, currencies):
    """
    Return a dataframe which as a column for each asset in the currencies ls
    these columns will have the balance change for each date
    """
    
    df['fee'] = df['fee'].astype('float')
    for currency in currencies:
        if currency not in df.columns:
            df[currency]=0
        df.loc[df.asset==currency, currency] = df[currency] + (df.fee*-1)
    
    df['amount'] = df['amount'].astype('float')
    for currency in list(set(fiat_currencies) & set(currencies)):
        if currency not in df.columns:
            df[currency]=0
            
        df.loc[(df.asset==currency) & (df.type=='deposit'),
               currency] = df[currency] + (df.amount)
        df.loc[(df.asset==currency) & (df.type=='withdrawal'), 
               currency] = df[currency] + (df.amount*-1)

    return df.groupby('date').agg('sum')[currencies]
    
def parse_api_results(resp, result_type):
    """
    Look at the results field of the API response.
    Result_type specifies the key within the response where the data lies.
    Returns as a dataframe
    """

    df = pd.DataFrame()
    if 'result' not in resp.json().keys():
        print(f"No result! Error: {resp.json()['error']}")
    for result in resp.json()['result'][result_type]:
        temp_df = pd.DataFrame(resp.json()['result'][result_type][result], index=[result])
        temp_df['time'] = pd.to_datetime(temp_df['time'], unit='s')
        temp_df['date'] = temp_df.time.dt.date.astype('datetime64')

        df = pd.concat([df,temp_df])
    return df

def load_key():
    if os.getenv('KEY') == None:
        key = input("""
Please enter password:
""")
        os.environ['KEY'] = key

    return os.environ['KEY'].encode('utf-8')

def generate_new_key():
    return Fernet.generate_key()

def encrypt(passw):
    key = load_key()
    cipher_suite = Fernet(key)
    return cipher_suite.encrypt(passw)
    
def decrypt(e_passw):
    key = load_key()
    cipher_suite = Fernet(key)
    return cipher_suite.decrypt(e_passw)