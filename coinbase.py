from config import daily_prices_ls, daily_prices_df, api_dict, pairs, accepted_currencies
from functions import parse_pairs_from_series, remap_series, remap_and_dedupe_assets, coinbase_aggregate_balances_per_day
from API_functions import coinbase_request, coinbase_parse_api_results, fetch_daily_price_pairs

import pandas as pd

def coinbase_accounts(api_key, api_sec):
    """
    Usng the api info, pulls the account details:
    Account balances and account IDs
    """
    r =  coinbase_request('accounts',{'limit' : 100,'order' : 'desc'}, api_key, api_sec)
    return r


def coinbase_transactions(api_key, api_sec):
    """
    Using the api details info:
    Pull transactions, create a DF with all balance changes by date
    Returns the DF aswell as the currencies included
    """
    r = coinbase_accounts(api_key, api_sec)

    # Loop through accounts and pull transactions
    df = pd.DataFrame()
    for account in r.json()['data']:
        if account['currency'] in accepted_currencies:            
            print(f"pulling transactions data for {account['currency']}")     
            rs = coinbase_request(f"accounts/{account['currency']}/transactions",
                                {'limit' : 100,'order' : 'desc'}, 
                                api_key, 
                                api_sec)
            tmp_df = coinbase_parse_api_results(rs)
            df = pd.concat([df, tmp_df], axis = 0, sort=False)
    
    # Split pairs into individual columns
    trades_df_pairs, pair_cols = parse_pairs_from_series(df.copy(),'pair')

    # Remap the old asset names
    # Find all currencies listed in the pairs
    currencies = []
    for pair in (pair_cols+['asset']):
        trades_df_pairs = remap_series(trades_df_pairs, pair)
        currencies += trades_df_pairs[pair].drop_duplicates().tolist()

    # dedupe them and remap if necessary
    currencies = remap_and_dedupe_assets(currencies)

    transactions_df_bare = coinbase_aggregate_balances_per_day(trades_df_pairs.copy(), currencies, pair_cols)
    return transactions_df_bare, currencies

def coinbase_balances(api_key, api_sec):
    """
    Pull Balances into a dataframe using the api creds
    Returns dict of balances
    """
    # Pull Balances
    r = coinbase_accounts(api_key, api_sec)

    account_balances = {}
    if r.status_code == 200: 
        if r.json()['data']:
            for acc in r.json()['data']:
                if float(acc['balance']['amount'])!=0:
                    account_balances[acc['balance']['currency']] = acc['balance']['amount']

    return account_balances

def coinbase_pull_all(api_key, api_sec, daily_prices_ls=daily_prices_ls, daily_prices_df=daily_prices_df ):
    """
    Process flow for all coinbase data
    Returns 
        - dataframe for balance changes by date
        - dataframe with daily price data for all associated assets traded within the API
        - dict with current balances
        - ls of currencies used
        - ls of successfully pulled daily prices
    """
    ## TRANSACTIONS DATA
    balance_df, currencies = coinbase_transactions(api_key, api_sec)
    
    ## DAILY PRICES
    daily_prices_df, daily_prices_ls = fetch_daily_price_pairs(pairs,'coinbase', daily_prices_ls, daily_prices_df)

    ## BALANCES
    account_balances_df = coinbase_balances(api_key, api_sec)

    return balance_df, daily_prices_df, account_balances_df, currencies, daily_prices_ls

if __name__ == "__main__":
    api_key = api_dict['Coinbase']['key']
    api_sec = api_dict['Coinbase']['sec']

    account_balances_df = coinbase_balances(api_key, api_sec)
    print(account_balances_df)