from config import daily_prices_ls, daily_prices_df, api_dict, pairs
from functions import parse_pairs_from_series, remap_series, remap_and_dedupe_assets, split_pair,  \
        kraken_aggregate_balances_per_day_ledger, kraken_aggregate_balances_per_day_trade
from API_functions import kraken_request, kraken_parse_api_results, fetch_daily_price_pairs

import time
import pandas as pd

def kraken_trades(api_key, api_sec):
    """
    Using the api details info, Pull trades, create a DataFrame with all balance changes by date

    Args:
        api_key (str): api key for the call
        api_sec (str): api secret for the call

    Returns:
        pandas.DataFrame: dataframe containing all the trades tied to the API credentials
        list: list of currencies in the data frame
    """
    # Pull trades
    resp = kraken_request('/0/private/TradesHistory', 
                        {"nonce": str(int(1000*time.time())),
                        "trades": True},
                        api_key,
                        api_sec)
    # Process trades
    trades_df = kraken_parse_api_results(resp, 'trades')

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
    trades_df_bare = kraken_aggregate_balances_per_day_trade(trades_df_pairs, currencies, pair_cols)

    return trades_df_bare, currencies

def kraken_ledger(api_key, api_sec, currencies):
    """
    Using the api details info, Ledger info (excluding trades) for all listed currencies,, create a DataFrame with all balance changes by date

    Args:
        api_key (str): api key for the call
        api_sec (str): api secret for the call
        currencies (list): list of currencies to pull ledger for 

    Returns:
        pandas.DataFrame: dataframe containing all the ledger info tied to the API credentials
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
        temp_df = kraken_parse_api_results(resp, 'ledger')
        temp_df = temp_df[temp_df.type != 'trade']    
        ledger_df = pd.concat([ledger_df,temp_df])
    
    # Rename assets + Remap if necessary
    ledger_df_asset = ledger_df.copy()
    ledger_df_asset['asset'] = ledger_df_asset.asset.apply(split_pair).apply(pd.Series)[0]
    ledger_df_asset = remap_series(ledger_df_asset, 'asset')

    # Aggregate 
    ledger_df_bare = kraken_aggregate_balances_per_day_ledger(ledger_df_asset, currencies)

    return ledger_df_bare

def kraken_balances(api_key, api_sec):
    """
    Usng the api info, pulls the account balances

    Args:
        api_key (str): api key for the call
        api_sec (str): api secret for the call

    Returns:
        dict: dictionary of assets and the associated balances
    """
    resp = kraken_request('/0/private/Balance',
                        {"nonce": str(int(1000*time.time()))},
                        api_key,
                        api_sec)

    account_balances = {}
    if resp.json()['result']:
        account_balances = resp.json()['result']

    return account_balances

# def kraken_pull_all(api_key, api_sec, daily_prices_ls=daily_prices_ls, daily_prices_df=daily_prices_df ):
def kraken_pull_all(api_key, api_sec, daily_prices_ls=[], daily_prices_df = pd.DataFrame()):
    """
    Process flow for all Kraken data

    Args:
        api_key (str): api key for the call
        api_sec (str): api secret for the call
        daily_prices_ls (list, optional): any pairs in this list will not be pulled again. Defaults to [].
        daily_prices_df (pandas.DataFrame(), optional): prices will be appended to this dataframe. Defaults to blank pandas.DataFrame().

    Returns:
        pandas.DataFrame: balance changes by date
        pandas.DataFrame: daily price data for all associated assets traded within the API
        dict: current balances
        list: currencies used
        list: successfully pulled daily prices
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
    daily_prices_df, daily_prices_ls = fetch_daily_price_pairs(pairs,'kraken',daily_prices_ls,daily_prices_df)

    ## BALANCES
    account_balances_df = kraken_balances(api_key, api_sec)

    return balance_df, daily_prices_df, account_balances_df, currencies, daily_prices_ls

if __name__ == "__main__":
    api_key = api_dict['Kraken']['key']
    api_sec = api_dict['Kraken']['sec']

    account_balances_df = kraken_balances(api_key, api_sec)
    print(account_balances_df)