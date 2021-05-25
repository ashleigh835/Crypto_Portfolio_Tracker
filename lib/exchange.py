import requests
import pandas as pd

from config import stable_coin_alts

class Exchange():    
    def request(self, uri_path):
        """
        API request to the api_url already within the class (self.api_url)

        Args:
            uri_path (str): sub path for the api call

        Returns:
            response: json response from the requests package (API)
        """
        return requests.get(f"{self.api_url}{uri_path}")
                          
    def getHistoricalPricesDataFrameList_Universal(self,symbols,native='USD',stable_coin_alt=True,stable_coin_alts=stable_coin_alts):
        """
        Retrieve historical price dataframe from the list of provided symbols.

        Args:
            symbols (list): list of symbols in the format of XXX/XXX e.g. ['BTC/USD','ETH/USD']
            native (str, optional): Asset ticker for the native currency used in the right side of the symbol. Defaults to 'USD'.
            stable_coin_alt (bool, optional): If the pairing failed, use the list of stable coin alternatives to find another pairing (e.g. if there was no reponse for USD, look for USDT). Defaults to True.
            stable_coin_alts (dict, optional): an alternative asset mapping to the given native, e.g. {'USD': ['USDT','DAI']}. Defaults to stable_coin_alts from config.py.

        Returns:
            Pandas.DataFrame: dataframe of price daily data in one column per symbol - indexed by date
        """
        hp_df = pd.DataFrame()
        for symbol in symbols:   
            
            # Treat staked symbols as their non-staked counterparts
            temp_symbol = symbol.replace('.S','')
            if temp_symbol.startswith('ETH2'):
                temp_symbol = temp_symbol.replace('ETH2','ETH')

            # If the non-staked counterpart is already in the dataframe, duplicate it instead of repulling
            if (symbol not in hp_df.columns) and (temp_symbol in hp_df.columns) and (symbol != temp_symbol):
                df = hp_df[[temp_symbol]].copy()  
                df = df.rename(columns={temp_symbol:symbol})
                hp_df = pd.concat([hp_df,df], axis = 1, sort=True, join='outer')
                
            elif temp_symbol not in hp_df.columns:
                print(f'new pair found! Pulling data for {symbol} ({temp_symbol})')
                df = self.getHistoricalPricesDataFrame_Universal(temp_symbol)
                # If activated (stable_coin_alt==True) and the above pull provided None, try pulling each alternative instead
                for stable_coin in stable_coin_alts[native]:
                    if stable_coin_alt and (df is None):
                        print(f"trying alternative: {symbol.replace(native,stable_coin)}")
                        df = self.getHistoricalPricesDataFrame_Universal(symbol.replace(native,stable_coin))
                        
                # e.g. if ETH was pulled for ETH2.S, then we should add both to prevent repulling ETH for ETH2 etc.
                if (symbol not in hp_df.columns) and (symbol != temp_symbol):
                    df[symbol] = df[temp_symbol].copy()
                    
                hp_df = pd.concat([hp_df,df], axis = 1, sort=True, join='outer')
        return hp_df