import hmac
import hashlib
import time
import requests
import pandas as pd
from requests.auth import AuthBase

from config import fiat_currencies
from lib.functions import decrypt
from lib.exchange import Exchange

class Coinbase(Exchange):
    def __init__(self, api_key, api_sec, key=''):
        """
        Args:
            api_key (utf8 str): api key
            api_sec (utf8 str): api secret
            key (str, optional): decryption key - if none provided, console will prompt for one and it will be stored in global variables (DEV ONLY). Defaults to ''.
        """
        self.api_url = 'https://api.coinbase.com/v2'
        self.api_url_pro = 'https://api.pro.coinbase.com'
        self.api_key = api_key
        self.api_sec = api_sec
        self.key = key      
        
    class WalletAuth(AuthBase):
        def __init__(self, api_key, api_sec, key):
            self.api_key = api_key
            self.api_sec = api_sec
            self.key = key   

        def __call__(self, request):
            """
            Creates an API signature to create an authorized API request for the provided url

            Args:
                request (requests.request): API Request.

            Returns:
                requests.request: updated with authorized headers 
            """      
            timestamp = str(int(time.time()))
            message = timestamp + request.method + request.path_url + (request.body or b'')
            signature = hmac.new(decrypt(self.api_sec,self.key), message.encode(), hashlib.sha256).hexdigest()

            request.headers.update({
                'CB-ACCESS-SIGN': signature,
                'CB-ACCESS-TIMESTAMP': timestamp,
                'CB-ACCESS-KEY': decrypt(self.api_key,self.key),
                'CB-VERSION': '2016-05-13'
            })
            return request 
            
    def auth_request(self, uri_path, data):
        """
        Submit an authenticated request to the API server

        Args:
            uri_path (str): sub path for the API call
            data (dict, optional): Data if necessary for the API call. Defaults to {}.

        Returns:
            response: json response from the requests package (API)
        """
        auth = self.WalletAuth(self.api_key, self.api_sec, self.key)
        return requests.get((self.api_url + uri_path),data=data,auth=auth)
    
    def getAccounts(self, refresh=False):
        """
        Get the Wallet-Accounts associated with the API account within the exchange
        
        Args:
            refresh (bool, optional): re-call the API function if the variable has not already been declared. Defaults to False.

        Returns:
            dict: response from the API, loaded into the self.accounts variable
        """
        if (refresh == True) or ('accounts' not in vars(self)):
            resp = self.auth_request('/accounts',{'limit' : 100,'order' : 'desc'})
            if resp.status_code == 200: 
                if 'result' in resp.json().keys():
                    self.accounts = resp.json()
                    return self.accounts
                elif 'error' in resp.json().keys():
                    for err in resp.json()['error']:
                        print(f"error: {err}")
            else: print(f"bad response: {resp.status_code} from API")
        else: return self.accounts
        
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
            accounts = self.getAccounts(refresh)
            bu = {}
            if accounts is not None:
                if 'data' in accounts.keys():
                    for acc in accounts['data']:
                        if float(acc['balance']['amount'])!=0: bu[acc['balance']['currency']] = acc['balance']['amount']
                self.balance_universal = bu
                return self.balance_universal
        else: return self.balance_universal
    
    def getValidAssets_Universal(self, refresh=False):
        """
        Get the valid assets within the exchange via API call
        UNIVERSAL - the output will be the same for functions with other exchange classes with the same definition name

        Args:
            refresh (bool, optional): re-call the API function if the variable has not already been declared. Defaults to False.

        Returns:
            list: response from the API, loaded into the self.validAssets_universal variable
        """
        if (refresh == True) or ('validAssets_universal' not in vars(self)):
            accounts = self.getAccounts(refresh)
            if accounts is not None:
                if 'data' in accounts.keys():
                    self.validAssets_universal = [account['currency'] 
                        for account in accounts['data'] 
                            if account['currency'] not in fiat_currencies
                    ]
                    return self.validAssets_universal
        else: return self.validAssets_universal
                      
    def getValidSymbols_Universal(self, native='USD', refresh=False):
        """
        Get the valid symbols within the exchange via API call
        UNIVERSAL - the output will be the same for functions with other exchange classes with the same definition name

        Args:
            refresh (bool, optional): re-call the API function if the variable has not already been declared. Defaults to False.

        Returns:
            list: response from the API, loaded into the self.validSymbols_universal variable
        """
        if (refresh == True) or ('validSymbols_universal' not in vars(self)):
            validAssets_Universal = self.getValidAssets_Universal(refresh)
            if validAssets_Universal is not None:
                self.validSymbols_universal =  [
                    f"{asset}/{native}" 
                        for asset in validAssets_Universal
                            if asset not in fiat_currencies
                ]
                return self.validSymbols_universal
        else: return self.validSymbols_universal
                     
    def getHistoricalPrices(self, symbol):
        """
        Get the recent Historical prices for the provided symbol within the exchange via API call

        Args:
            symbol (str): trading symbol as XXX/XXX

        Returns:
            dict: response from the API
        """
        resp = self.request(f"/products/{symbol.replace('/','-')}/candles?granularity=86400")
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
            df = pd.DataFrame(historicalPrices, columns=['unix', 'low', 'high', 'open', 'close', 'volume'])
            df['date'] = pd.to_datetime(df['unix'], unit='s')  
            df['volume_from'] = df['volume'].astype(float) * df['close'].astype(float)     
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
        transactions = self.getTransactions(refresh)    
        if transactions is not None:
            if transactions.empty == False:
                assets = [f"{asset}/{native}" for asset in transactions[~transactions.asset.isna()].asset.drop_duplicates().tolist()]
                pairs = transactions[~transactions.pair.isna()].pair.drop_duplicates().tolist()
                symbols = list(set(assets+pairs))
                return self.getHistoricalPricesDataFrameList_Universal(symbols, native, stable_coin_alt) 
               
#         type fiat_deposit not supported!             
    def parse_api_results(self,resp):
        """
        Parse Ledger or Trade results into a formatted dataframe

        Args:
            resp (dict): dictionary from the API json response

        Returns:
            pandas.DataFrame: formatted dataframe of the handled resp
        """
        df = pd.DataFrame()
        if 'data' not in resp.keys():
            print(f"No result! Error: {resp['error']}")
            return None
        for data in resp['data']:
            tmp = {}
            for ele in ['type','created_at','resource']:
                tmp[ele] = data[ele]

            if data['type']=='buy':
                tmp['vol']=data['amount']['amount']
                tmp['cost']=data['native_amount']['amount']
                tmp['pair']=data['amount']['currency']+'/'+data['native_amount']['currency']

            elif data['type'] == 'trade':
                tmp['vol']=data['amount']['amount'] 
                tmp['cost']=0                              
                tmp['asset']=data['amount']['currency']
                tmp['t_id']=data['trade']['id']

            elif data['type']=='send':
                if data['network']['status'] in ['confirmed','unconfirmed']:
                    if float(data['amount']['amount'])<0:
                        tmp['vol']=float(data['network']['transaction_amount']['amount'])*-1
                    else:
                        tmp['vol']=float(data['network']['transaction_amount']['amount'])
                    tmp['cost']=0        
                    tmp['asset']=data['amount']['currency']
                    tmp['fee']=data['network']['transaction_fee']['amount']
                    tmp['t_id']=data['network']['hash']
                elif data['network']['status'] == 'off_blockchain':              
                    tmp['vol']=data['amount']['amount']
                    tmp['cost']=0                         
                    tmp['asset']=data['amount']['currency']
                else:
                    print(f"Transactions: {data['type']}, network status: {data['network']['status']} not supported!")  

            elif data['type']== 'staking_reward':
                tmp['vol']=data['amount']['amount']
                tmp['cost']=0      

            else:
                print(f"type {data['type']} not supported!")

            tmp_df = pd.DataFrame(tmp, index=[data['id']])
            tmp_df['date'] = pd.to_datetime(tmp_df.created_at).dt.date.astype('datetime64')
            df = pd.concat([df, tmp_df], axis = 0, sort=False)

        return df
    
    def getWalletTransactions(self, account):
        """
        pulls the transactions associated with the API wallet account on the exchange into a dataframe

        Args:
            account (str): account id (from the accounts API call)

        Returns:
            dict: response from the API
        """        
        resp = self.auth_request(f'/accounts/{account}/transactions', {'limit' : '100','order' : 'desc'})
        if resp.status_code == 200: 
            if 'result' in resp.json().keys():
                return resp.json()
            elif 'error' in resp.json().keys():
                for err in resp.json()['error']:
                    print(f"error: {err}")
            else: print(f"no results in API response")
        else: 
            print(f"bad response: {resp.status_code} from API")
            return None    
                      
    def getTransactions(self,refresh=False):
        """
        pulls the transactions associated with all accounts within the API wallet account on the exchange into a dataframe

        Args:
            refresh (bool, optional): re-call the API function if the variable has not already been declared. Defaults to False.

        Returns:
            pandas.DataFrame: response from the API, loaded into the self.transactions variable
        """   
        if (refresh == True) or ('/transactions' not in vars(self)):
            df=pd.DataFrame()
            accounts = self.getAccounts(refresh)
            if accounts is not None:
                if 'data' in accounts.keys():
                    for acc in accounts['data']:
                        print(f"pulling transactions for {acc['name']}")
                        if acc['currency'] not in fiat_currencies:   
                            resp = self.getWalletTransactions(acc['id'])
                            tmp_df = self.parse_api_results(resp)
                            df = pd.concat([df, tmp_df], axis = 0, sort=False)
                    self.transactions = df
                    return self.transactions
        else: return self.transactions