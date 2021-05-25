import hmac
import hashlib
import urllib
import time
import requests
import pandas as pd
import base64

from config import fiat_currencies
from lib.functions import decrypt, parse_pairs_from_series, rename_asset
from lib.exchange import Exchange

class Kraken(Exchange):
    def __init__(self, api_key, api_sec, key=''):
        """
        Args:
            api_key (utf8 str): api key
            api_sec (utf8 str): api secret
            key (str, optional): decryption key - if none provided, console will prompt for one and it will be stored in global variables (DEV ONLY). Defaults to ''.
        """
        self.api_url = 'https://api.kraken.com'
        self.api_key = api_key
        self.api_sec = api_sec
        self.key = key      
        
    def sign_request(self, uri_path, data):  
        """
        Creates an API signature to create an authorized API request for the provided url

        Args:
            uri_path (str): sub path for the aPI call
            data (dict): data body for the API request. Defaults to ''.

        Returns:
            hexidecimal key: API hexidecimal signature 
        """      
        postdata = urllib.parse.urlencode(data)
        encoded = (str(data['nonce']) + postdata).encode()
        message = uri_path.encode() + hashlib.sha256(encoded).digest()
        mac = hmac.new(base64.b64decode(decrypt(self.api_sec,self.key)), message, hashlib.sha512)
        return base64.b64encode(mac.digest()).decode()
            
    def auth_request(self, uri_path, data={}):
        """
        Submit an authenticated request to the API server

        Args:
            uri_path (str): sub path for the API call
            data (dict, optional): Data if necessary for the API call. Defaults to {}.

        Returns:
            response: json response from the requests package (API)
        """
        data['nonce']=str(int(1000*time.time()))
        headers = {}
        headers['Api-Key'] = decrypt(self.api_key,self.key)
        headers['API-Sign'] = self.sign_request(uri_path, data)   
        return requests.post(f"{self.api_url}{uri_path}", headers=headers, data=data)
    
    def getBalances_Universal(self, refresh=False):
        """
        Get the Balances for each account associated with the API account within the exchange
        UNIVERSAL - the output will be the same for functions with other exchange classes with the same definition name

        Args:
            refresh (bool, optional): re-call the API function if the variable has not already been declared. Defaults to False.

        Returns:
            dict: response from the API, loaded into the self.balance_universal variable
        """
        if refresh or ('balance_universal' not in vars(self)):
            resp = self.auth_request('/0/private/Balance')
            if resp.status_code == 200: 
                if 'result' in resp.json().keys():
                    bu = {}
                    for balance in resp.json()['result']:
                        bu[rename_asset(balance, self.getValidAssets_Universal())] = resp.json()['result'][balance]
                    self.balance_universal = bu
                    return self.balance_universal
                elif 'error' in resp.json().keys():
                    for err in resp.json()['error']:
                        print(f"error: {err}")
            else: print(f"bad response: {resp.status_code} from API")
        else: return self.balance_universal
                                  
    def getValidSymbols(self, refresh=False):
        """
        Get the valid symbols within the exchange via API call

        Args:
            refresh (bool, optional): re-call the API function if the variable has not already been declared. Defaults to False.

        Returns:
            dict: response from the API, loaded into the self.validSymbols variable
        """
        if refresh or ('validSymbols' not in vars(self)):
            resp = self.request('/0/public/AssetPairs')
            if resp.status_code == 200:
                if 'result' in resp.json().keys():
                    self.validSymbols = resp.json()['result']
                    return self.validSymbols
                elif 'error' in resp.json().keys():
                    for err in resp.json()['error']:
                        print(f"error: {err}")
        else: return self.validSymbols
                              
    def getValidSymbols_Universal(self, refresh=False):
        """
        Get the valid symbols within the exchange via API call
        UNIVERSAL - the output will be the same for functions with other exchange classes with the same definition name

        Args:
            refresh (bool, optional): re-call the API function if the variable has not already been declared. Defaults to False.

        Returns:
            list: response from the API, loaded into the self.validSymbols_universal variable
        """
        if refresh or ('validSymbols_universal' not in vars(self)):
            validSymbols = self.getValidSymbols(refresh)
            if validSymbols is not None:
                self.validSymbols_universal = [validSymbols[symbol]['wsname']
                    for symbol in validSymbols
                        if 'wsname' in validSymbols[symbol].keys()
                ]
                return self.validSymbols_universal
        else: return self.validSymbols_universal
               
    def getValidAssets_Universal(self, refresh=False):
        """
        Get the valid assets within the exchange via API call (uses the valid Symbols APIs and takes the left pairing)
        UNIVERSAL - the output will be the same for functions with other exchange classes with the same definition name

        Args:
            refresh (bool, optional): re-call the API function if the variable has not already been declared. Defaults to False.

        Returns:
            list: response from the API, loaded into the self.validAssets_universal variable
        """
        if (refresh == True) or ('validAssets_universal' not in vars(self)):
            validSymbols_universal = self.getValidSymbols_Universal(refresh)
            if validSymbols_universal is not None:
                self.validAssets_universal = list(set([symbol.split('/')[0] for symbol in validSymbols_universal]))
                return self.validAssets_universal
        else: return self.validAssets_universal

    def getHistoricalPrices(self, symbol):
        """
        Get the recent Historical prices for the provided symbol within the exchange via API call

        Args:
            symbol (str): trading symbol as XXX/XXX

        Returns:
            dict: response from the API
        """
        pair_split = symbol.split('/')
        symbol = pair_split[0] + pair_split[1]
        resp = self.request(f'/0/public/OHLC?pair={symbol}&interval=1440')
        if resp.status_code == 200: 
            if 'result' in resp.json().keys():
                return resp.json()
            elif 'error' in resp.json().keys():
                for err in resp.json()['error']:
                    print(f"error: {err}")
        else: print(f"bad response: {resp.status_code} from API")   
    
    def getHistoricalPricesDataFrame(self,symbol):
        """
        Get the recent Historical prices for the provided symbol within the exchange via API call

        Args:
            symbol (str): trading symbol as XXX/XXX

        Returns:
            pandas.DataFrame: response from the API
        """
        historicalPrices = self.getHistoricalPrices(symbol)        
        if historicalPrices is not None:    
            if 'result' in historicalPrices.keys():  
                keys=[]
                for item in historicalPrices['result']:
                    keys.append(item)
                if keys[0] != 'last':
                    df = pd.DataFrame(historicalPrices['result'][keys[0]],columns=['unix', 'open', 'high', 'low', 'close', 'vwap', 'volume', 'tradecount'])
                else:
                    df = pd.DataFrame(historicalPrices['result'][keys[1]],columns=['unix', 'open', 'high', 'low', 'close', 'vwap', 'volume', 'tradecount'])
                df['date'] = pd.to_datetime(df['unix'], unit='s')
                return df
            elif 'error' in historicalPrices.keys():
                for err in historicalPrices['error']:
                    print(f"error: {err}")
    
    def getHistoricalPricesDataFrame_Universal(self,symbol):
        """
        Get the recent Historical prices for the provided symbol within the exchange via API call
        UNIVERSAL - the output will be the same for functions with other exchange classes with the same definition name

        Args:
            symbol (str): trading symbol as XXX/XXX

        Returns:
            pandas.DataFrame: response from the API
        """
        df = self.getHistoricalPricesDataFrame(symbol)
        if df is not None:
            if df.empty == False:
                df[symbol] = (df['high'].astype(float)+df['low'].astype(float))/2  
                df = df[['date',symbol]].set_index('date')
                return df
        
    def getHistoricalPricesForNonZeroBalances_Universal(self,native='USD',stable_coin_alt=True,refresh=False):
        """
        Get the recent Historical prices for any assets where the current balance within the exchange for that asset is not zero
        UNIVERSAL - the output will be the same for functions with other exchange classes with the same definition name

        Args:
            native (str, optional): Asset ticker for the native currency used in the right side of the symbol. Defaults to 'USD'.
            stable_coin_alt (bool, optional): If the pairing failed, use the list of stable coin alternatives to find another pairing (e.g. if there was no reponse for USD, look for USDT). Defaults to True.
            refresh (bool, optional): re-call the API function if the variable has not already been declared. Defaults to False.

        Returns:
            Pandas.DataFrame: dataframe of price daily data in one column per symbol - indexed by date
        """
        balances = self.getBalances_Universal(refresh)       
        if balances is not None:
            balances_to_use = [f"{asset}/USD" for asset in balances if asset not in fiat_currencies]
            return self.getHistoricalPricesDataFrameList_Universal(balances_to_use, native, stable_coin_alt) 
          
    def getHistoricalPricesForTransactionWallets_Universal(self,native='USD',stable_coin_alt=True,refresh=False):
        """
        Get the recent Historical prices for any assets which have been traded through this account within the exchange
        UNIVERSAL - the output will be the same for functions with other exchange classes with the same definition name

        Args:
            native (str, optional): Asset ticker for the native currency used in the right side of the symbol. Defaults to 'USD'.
            stable_coin_alt (bool, optional): If the pairing failed, use the list of stable coin alternatives to find another pairing (e.g. if there was no reponse for USD, look for USDT). Defaults to True.
            refresh (bool, optional): re-call the API function if the variable has not already been declared. Defaults to False.

        Returns:
            Pandas.DataFrame: dataframe of price daily data in one column per symbol - indexed by date
        """
        walletLedger = self.getLedger(refresh)
        walletTrades, pair_cols = self.getTradesPairs(refresh)
        asset_ls=[]
        if walletLedger is not None:
            asset_ls = walletLedger.asset.drop_duplicates().tolist()
        if walletTrades is not None:
            for pair in pair_cols: asset_ls += walletTrades[pair].drop_duplicates().tolist()
        symbols =  list(set(
            [f"{rename_asset(asset, self.getValidAssets_Universal())}/USD" 
                 for asset in asset_ls
                    if rename_asset(asset, self.getValidAssets_Universal()) not in fiat_currencies
            ]
        ))
        return self.getHistoricalPricesDataFrameList_Universal(symbols, native, stable_coin_alt) 
        
    def parse_api_results(self,resp):
        """
        Parse Ledger or Trade results into a formatted dataframe

        Args:
            resp (dict): dictionary from the API json response

        Returns:
            pandas.DataFrame: formatted dataframe of the handled resp
        """
        df = pd.DataFrame()
        for result in resp:
            temp_df = pd.DataFrame(resp[result], index=[result])
            temp_df['time'] = pd.to_datetime(temp_df['time'], unit='s')
            temp_df['date'] = temp_df.time.dt.date.astype('datetime64')
            df = pd.concat([df,temp_df], axis=0)
        return df
                  
    def getTrades(self, refresh=False): 
        """
        pulls the Trades associated with the API account on the exchange into a dataframe

        Args:
            refresh (bool, optional): re-call the API function if the variable has not already been declared. Defaults to False.

        Returns:
            pandas.DataFrame: response from the API, loaded into the self.walletTrades variable
        """            
        if refresh or ('walletTrades' not in vars(self)):   
            resp = self.auth_request('/0/private/TradesHistory',{"trades": True})
            if resp.status_code == 200:
                if 'result' in resp.json().keys():
                    if 'trades' in resp.json()['result'].keys():
                        self.walletTrades = self.parse_api_results(resp.json()['result']['trades'])
                        return self.walletTrades
                elif 'error' in resp.json().keys():
                    for err in resp.json()['error']:
                        print(f"error: {err}")
                else: print(f"no results in API response")
            else: print(f"bad response: {resp.status_code} from API")
        else: return self.walletTrades
                                                
    def getTradesPairs(self, refresh=False):
        """
        pulls the Trades associated with the API account on the exchange into a dataframe. Dataframe includes two columns representing the assets in the trading symbol

        Args:
            refresh (bool, optional): re-call the API function if the variable has not already been declared. Defaults to False.

        Returns:
            pandas.DataFrame: response from the API, loaded into the self.walletTrades variable
        """            
        walletTrades = self.getTrades(refresh)
        if walletTrades is not None:
            return parse_pairs_from_series(walletTrades,'pair',self.getValidAssets_Universal(refresh))       
    
    def getLedger(self, refresh=False):
        """
        pulls the ledger (excluding trades) associated with the API account on the exchange into a dataframe

        Args:
            refresh (bool, optional): re-call the API function if the variable has not already been declared. Defaults to False.

        Returns:
            pandas.DataFrame: response from the API, loaded into the self.walletTrades variable
        """       
        if refresh or ('walletLedger' not in vars(self)):   
            resp = self.auth_request('/0/private/Ledgers')
            if resp.status_code == 200:
                if 'result' in resp.json().keys():
                    if 'ledger' in resp.json()['result'].keys():
                        df = self.parse_api_results(resp.json()['result']['ledger'])
                        if df.empty == False:
                            df = df[df.type != 'trade']      
                            self.walletLedger = df[df.type != 'trade'].copy()
                            return self.walletLedger  
                elif 'error' in resp.json().keys():
                    for err in resp.json()['error']:
                        print(f"error: {err}")
            else: print(f"bad response: {resp.status_code} from API")
        else: return self.walletLedger 
                                                