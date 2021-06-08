import pandas as pd

from lib.exchange import Exchange

class CoinGecko(Exchange):
    def __init__(self):
        self.api_url = 'https://api.coingecko.com/api/v3'
    
    def getCoinList(self, refresh=False):
        """
        Get the valid assets within the exchange via API call

        Args:
            refresh (bool, optional): re-call the API function if the variable has not already been declared. Defaults to False.

        Returns:
            pandas.DataFrame(): response from the API, loaded into the self.coinList variable
        """
        if (refresh == True) or ('coinList' not in vars(self)):
            resp = self.request('/coins/list?')
            if resp.status_code == 200: 
                if len(resp.json())>0:
                    self.coinList = pd.DataFrame(resp.json()).set_index('id')
                    return self.coinList
            else: print(f"bad response: {resp.status_code} from API")
        else: return self.coinList
    
    def getSymbolID(self, symbol, refresh=False):
        """
        Get the ID for the symbol within the exchange

        Args:
            symbol (str): symbol to retrieve the coingecko specific asset ID for
            refresh (bool, optional): re-call the API function if the variables used have not already been declared. Defaults to False.

        Returns:
            pandas.DataFrame(): response from the API
        """
        coinList = self.getCoinList(refresh)
        if coinList is not None: 
            df = coinList[coinList.symbol == symbol.lower()]
            if df.empty==False:
                return df.index.values[0]  
            
    def getSymbolIDs(self, symbols, refresh=False):
        """
        Get the IDs for the symbols within the exchange

        Args:
            symbol (str): symbol to retrieve the coingecko specific asset ID for
            refresh (bool, optional): re-call the API function if the variables used have not already been declared. Defaults to False.

        Returns:
            pandas.DataFrame(): response from the API
        """
        coinList = self.getCoinList(refresh)
        if coinList is not None: 
            df = coinList[coinList.symbol.str.upper().isin(symbols)]
            if df.empty==False:
                return df.reset_index().set_index('symbol')[['id']]     
    
    def getSymbolPrice(self, symbol, native='USD', refresh=False):
        """
        Get the spot price for the symbol within the exchange

        Args:
            symbol (str): symbol to retrieve the coingecko specific asset ID for
            native (str): currency to use as the price comparison in the spot price
            refresh (bool, optional): re-call the API function if the variables used have not already been declared. Defaults to False.

        Returns:
            dict: price from API
        """
        symbolID = self.getSymbolID(symbol, refresh)
        resp = self.request(f'/simple/price?ids={symbolID}&vs_currencies={native.lower()}')
        if resp.status_code == 200: 
            if symbolID in resp.json().keys():
                return {f"{symbol}/{native}".upper(): resp.json()[symbolID][native.lower()]}
        else: print(f"bad response: {resp.status_code} from API")
    
    def getSymbolPrices(self, symbols, native='USD', refresh=False):
        """
        Get the spot prices for the symbols within the exchange

        Args:
            symbols (str): symbol to retrieve the coingecko specific asset ID for
            native (str): currency to use as the price comparison in the spot price
            refresh (bool, optional): re-call the API function if the variables used have not already been declared. Defaults to False.

        Returns:
            dict: price from API
        """
        symbolIDs = self.getSymbolIDs(symbols,refresh)
        if symbolIDs is not None:
            coinList = self.getCoinList(refresh)
            symbols_str = ','.join(symbolIDs.id.drop_duplicates())
            resp = self.request(f'/simple/price?ids={symbols_str}&vs_currencies={native.lower()}')
            if resp.status_code == 200: 
                prices = {}
                for symbolID in resp.json():
                    prices[f"{coinList.at[symbolID,'symbol']}/{native}".upper()] = resp.json()[symbolID][native.lower()]
                return prices
            else: print(f"bad response: {resp.status_code} from API")
            
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
            coinList = self.getCoinList(refresh)
            if coinList is not None: 
                self.validSymbols_universal = [f"{asset.upper()}/USD" for asset in coinList.symbol.drop_duplicates()]
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
