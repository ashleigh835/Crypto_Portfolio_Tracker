from config import *

from packages import *
from functions import * 
from API_functions import * 

def kraken_trades(api_key, api_sec):
    """
    Using the api details info:
    Pull Trades, create a DF with all balance changes by date
    Returns the DF aswell as the currencies included
    """

    # Pull trades
    resp = kraken_request('/0/private/TradesHistory', 
                        {"nonce": str(int(1000*time.time())),
                        "trades": True},
                        api_key,
                        api_sec)
    # Process trades
    trades_df = parse_api_results(resp, 'trades')

    # Split pairs into individual columns
    trades_df_pairs, pair_cols = parse_pairs_from_series(trades_df.copy(),'pair')

    # Remap the old asset names
    # Find all currencies listed in the pairs
    currencies = []
    for pair in pair_cols:
        trades_df_pairs = remap_series(trades_df_pairs, pair)
        currencies += trades_df_pairs[pair].drop_duplicates().tolist()
        
    # dedupe them and remap if necessary
    currencies = remap_and_dedupe_assets(currencies)

    # Aggregate 
    trades_df_bare = aggregate_balances_per_day_trade(trades_df_pairs, currencies, pair_cols)

    return trades_df_bare, currencies

def kraken_ledger(api_key, api_sec, currencies):
    """
    Using the api details info:
    Pull Ledger info (excluding trades) for all listed currencies, create a DF with all balance changes by date
    Returns the DF
    """

    # Pull Ledger (includes withdrawals and deposits)
    # We need this to include any fees, even when we were just moving shit about
    ledger_df = pd.DataFrame()
    for asset in currencies:
        resp = kraken_request('/0/private/Ledgers',
                            {"nonce": str(int(1000*time.time())),
                            "asset": asset,
                            "start": 1610124514},
                            api_key, 
                            api_sec)
        # Process ledger
        temp_df = parse_api_results(resp, 'ledger')
        temp_df = temp_df[temp_df.type != 'trade']    
        ledger_df = pd.concat([ledger_df,temp_df])
    
    # Rename assets + Remap if necessary
    ledger_df_asset = ledger_df.copy()
    ledger_df_asset['asset'] = ledger_df_asset.asset.apply(split_pair).apply(pd.Series)[0]
    ledger_df_asset = remap_series(ledger_df_asset, 'asset')

    # Aggregate 
    ledger_df_bare = aggregate_balances_per_day_ledger(ledger_df_asset, currencies)

    return ledger_df_bare

def kraken_daily_prices(pairs=pairs, dta=kraken_daily_prices_df):
    """
    PULL DAILY PRICES FOR SPECIFIC PAIRS (This is a public API - doesn't need credentials)
    RETURNS A DICTIONARY WITH KEY: PAIR AND VALUE = DATAFRAME OF THE DAILY DATA
    """
    for pair in pairs:
        if pair not in dta.keys():
            print(f'new pair found! Pulling data for {pair}')
        dta[pair] = fetch_OHLC_data(symbol=pair, timeframe='1440')  # fetches daily data

    # Concat all into one dataframe
    daily_values_df = pd.DataFrame()
    for pair in pairs:
        tmpdf = dta[pair].copy()[['date','high','low']]  
        tmpdf['high'] = tmpdf['high'].astype(float)
        tmpdf['low'] = tmpdf['low'].astype(float)
        tmpdf[pair] = (tmpdf['high']+tmpdf['low'])/2  
        
        tmpdf = tmpdf[['date',pair]].set_index('date')
        daily_values_df = pd.concat([daily_values_df,tmpdf], axis = 1, sort=True, join='outer')
    
    return daily_values_df, dta

def kraken_balances(api_key, api_sec):
    """
    Pull Balances into a dataframe using the api creds
    Returns dict of balances
    """
    # Pull Balances
    resp = kraken_request('/0/private/Balance',
                        {"nonce": str(int(1000*time.time()))},
                        api_key,
                        api_sec)

    account_balances = {}
    if resp.json()['result']:
        account_balances = resp.json()['result']

    return account_balances

def kraken_pull_all(api_key, api_sec):
    """
    Process flow for all Kraken data
    Returns 
        - dataframe for balance changes by date
        - dataframe with daily price data for all associated assets traded within the API
        - dict with current balances
        - ls of currencies used
    """

    ## TRADES DATA
    trades_df_bare, currencies = kraken_trades(api_key, api_sec)

    ## LEDGER DATA
    ledger_df_bare = kraken_ledger(api_key, api_sec, currencies)

    ## COMBINE LEDGER AND TRADES
    # combine data
    balance_df = pd.concat([ledger_df_bare,trades_df_bare], axis=0)
    balance_df = balance_df.groupby('date').agg(sum)
    
    ## DAILY PRICES
    daily_values_df, kraken_daily_prices_df = kraken_daily_prices(pairs)

    ## BALANCES
    account_balances_df = kraken_balances(api_key, api_sec)

    return balance_df, daily_values_df, account_balances_df, currencies

if __name__ == "__main__":
    api_key = api_dict['Kraken']['key']
    api_sec = api_dict['Kraken']['sec']

    account_balances_df = kraken_balances(api_key, api_sec)
    print(account_balances_df)