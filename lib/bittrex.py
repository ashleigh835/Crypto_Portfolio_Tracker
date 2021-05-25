import hmac
import hashlib
import urllib
import time
import requests
import pandas as pd

from config import fiat_currencies
from lib.functions import decrypt
from lib.exchange import Exchange

class Bittrex(Exchange):
    def __init__(self, api_key, api_sec, key=''):
        """
        Args:
            api_key (utf8 str): api key
            api_sec (utf8 str): api secret
            key (str, optional): decryption key - if none provided, console will prompt for one and it will be stored in global variables (DEV ONLY). Defaults to ''.
        """
        self.api_url = 'https://api.bittrex.com/v3'
        self.api_key = api_key
        self.api_sec = api_sec
        self.key = key

    def sign_request(self, timestamp, url, method, contenthash=b''):
        """
        Creates an API signature to create an authorized API request for the provided url

        Args:
            timestamp (str): Used as a nonce - should be str(int(1000*time.time())) and match the API-Timestamp header in the request outside of this function
            url (str): full url of the API request
            method (str): method of the API request e.g. POST, GET etc. 
            contenthash (bytes, optional): data body for the API request. Defaults to b''.

        Returns:
            hexidecimal key: API hexidecimal signature 
        """
        message = timestamp + url + method.upper() + contenthash
        sigdigest = hmac.new(decrypt(self.api_sec,self.key), message.encode(), hashlib.sha512).hexdigest()
        return sigdigest.upper()
        
    def auth_request(self, uri_path, data={}):
        """
        Submit an authenticated request to the API server

        Args:
            uri_path (str): sub path for the aPI call
            data (dict, optional): Data if necessary for the API call. Defaults to {}.

        Returns:
            response: json response from the requests package (API)
        """
        timestamp = str(int(1000*time.time()))
        contenthash = hashlib.sha512(urllib.parse.urlencode(data).encode()).hexdigest()
        sign = self.sign_request(timestamp, (self.api_url + uri_path), 'GET', contenthash)    

        headers = {}
        headers['Api-Key'] = decrypt(self.api_key,self.key)
        headers['Api-Timestamp'] = timestamp
        headers['Api-Content-Hash'] = contenthash
        headers['Api-Signature'] = sign

        return requests.get(f"{self.api_url}{uri_path}", headers=headers)

    def getBalances(self, refresh=False):
        """
        Get the Balances for each account associated with the API account within the exchange

        Args:
            refresh (bool, optional): re-call the API function if the variable has not already been declared. Defaults to False.

        Returns:
            dict: response from the API, loaded into the self.balances variable
        """
        if (refresh == True) or ('balances' not in vars(self)):
            resp = self.auth_request('/balances')
            if resp.status_code == 200: 
                if 'result' in resp.json().keys():
                    self.balances = resp.json()
                    return self.balances
                elif 'error' in resp.json().keys():
                    for err in resp.json()['error']:
                        print(f"error: {err}")
            else: print(f"bad response: {resp.status_code} from API")
        else: return self.balances
        
    def getBalances_Universal(self, refresh=False):
        """
        Get the Balances for each account associated with the API account within the exchange
        UNIVERSAL - the output will be the same for functions with other exchange classes with the same definition name

        Args:
            refresh (bool, optional): re-call the API function if the variable has not already been declared. Defaults to False.

        Returns:
            dict: response from the API, loaded into the self.balance_universal variable
        """
        if (refresh == True) or ('balance_universal' not in vars(self)):
            balances = self.getBalances(refresh)
            bu = {}
            if balances is not None:
                for balance in balances:
                    if float(balance['total'])!=0 : bu[balance['currencySymbol']] = balance['total']
            self.balance_universal = bu
            return self.balance_universal
        else: return self.balance_universal
    
    def getValidSymbols(self, refresh=False):
        """
        Get the valid symbols within the exchange via API call

        Args:
            refresh (bool, optional): re-call the API function if the variable has not already been declared. Defaults to False.

        Returns:
            dict: response from the API, loaded into the self.validSymbols variable
        """
        if (refresh == True) or ('validSymbols' not in vars(self)):
            resp = self.request('/markets/tickers')
            if resp.status_code == 200: 
                if 'result' in resp.json().keys():
                    self.validSymbols = resp.json()
                    return self.validSymbols
                elif 'error' in resp.json().keys():
                    for err in resp.json()['error']:
                        print(f"error: {err}")
            else: print(f"bad response: {resp.status_code} from API")
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
        if (refresh == True) or ('validSymbols_universal' not in vars(self)):
            validSymbols = self.getValidSymbols(refresh)
            su = []
            if validSymbols is not None:
                for symbol in validSymbols:
                    su += [symbol['symbol']]
            self.validSymbols_universal = su
            return self.validSymbols_universal
        else: return self.validSymbols_universal

    def getValidAssets_Universal(self, refresh=False):
        """
        Get the valid assets within the exchange via API call (uses the valid Symbols APIs and takes the left pairing)
        UNIVERSAL - the output will be the same for functions with other exchange classes with the same definition name

        Args:
            refresh (bool, optional): re-call the API function if the variable has not already been declared. Defaults to False.

        Returns:
            list: response from the API, loaded into the self.validSymbols_universal variable
        """
        if (refresh == True) or ('validAssets_universal' not in vars(self)):
            validSymbols_universal = self.getValidSymbols_Universal(refresh)
            if validSymbols_universal is not None:
                self.validAssets_universal = list(set([symbol.split('-')[0] for symbol in validSymbols_universal]))
                return self.validAssets_universal
        else: return self.validAssets_universal
        
    def getHistoricalPrices(self, symbol):
        """
        Get the recent Historical prices for the provided symbol within the exchange via API call

        Args:
            symbol (str): trading symbol as XXX-XXX

        Returns:
            dict: response from the API
        """
        if symbol in self.getValidSymbols_Universal(False): 
            # resp = self.request(f"/markets/{symbol}/candles/DAY_1/historical/{year}")
            resp = self.request(f"/markets/{symbol}/candles/DAY_1/recent")
            if resp.status_code == 200: 
                if 'result' in resp.json().keys():
                    return resp.json()
                elif 'error' in resp.json().keys():
                    for err in resp.json()['error']:
                        print(f"error: {err}")
            else: print(f"bad response: {resp.status_code} from API")   
        else:
            print(f"symbol {symbol} not a valid symbol for this exchange")
            return None
    
    def getHistoricalPricesDataFrame(self,symbol):
        """
        Get the recent Historical prices for the provided symbol within the exchange via API call

        Args:
            symbol (str): trading symbol as XXX-XXX

        Returns:
            pandas.DataFrame: response from the API
        """
        historicalPrices = self.getHistoricalPrices(symbol)        
        if historicalPrices is not None:
            df = pd.DataFrame(historicalPrices, columns=['startsAt', 'open', 'high', 'low', 'close'])
            df['date'] = pd.to_datetime(df.startsAt)
            return df
    
    def getHistoricalPricesDataFrame_Universal(self,symbol):
        """
        Get the recent Historical prices for the provided symbol within the exchange via API call
        UNIVERSAL - the output will be the same for functions with other exchange classes with the same definition name

        Args:
            symbol (str): trading symbol as XXX/XXX

        Returns:
            pandas.DataFrame: response from the API
        """
        df = self.getHistoricalPricesDataFrame(symbol.replace('/','-'))
        if df is not None:
            if df.empty == False:
                df[symbol.replace('-','/')] = (df['high'].astype(float)+df['low'].astype(float))/2  
                df = df[['date',symbol.replace('-','/')]].set_index('date')
                df.index = df.index.tz_convert(None)
            return df
        else: return df
            
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
            balances_to_use = [f"{asset}-USD" for asset in balances if asset not in fiat_currencies]
            return self.getHistoricalPricesDataFrameList_Universal(balances_to_use,native,stable_coin_alt)  
        else: return balances                 