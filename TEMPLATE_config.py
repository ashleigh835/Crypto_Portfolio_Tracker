import os

# MANUAL INPUTS
accepted_currencies = ['XDG',
                       'DOGE',
                       'USD',
                       'XMR',
                       'BTC',
                       'XBT',
                       'ETH',
                       'ADA',
                       'DOT']

fiat_currencies = ['USD','GBP']

pairs = ["DOGE/USD","XMR/USD","ADA/USD","BTC/USD","DOT/USD","ETH/USD"]

# STATIC VARIABLES

## If os.environ['ENCRYPT'] = True, the following metrics will prompt for a decryption key
## These can be generated from your original key by:
#       using the generate_new_key() function (the same key will be used indefinately so write it down)
#       using the encrypt(key) function with the key 
os.environ['ENCRYPT'] = 'True'
# If encrypted, please encode to utf-8 (or wrap string in b'')api_dict = {
api_dict = {
    'Coinbase' : {'sec' : b'',
                  'key' : b''
                  },   
    'Coinbase Pro' : {'sec' : b'',
                  'key' : b''
                  },   
    'Kraken' : {'sec' : b'',
                'key' : b''
                }
}
## END OF ENCRYPTED VARIABLES

remap_assets = {'XDG':'DOGE',
                'XBT':'BTC'}

# Declare initial variables
kraken_daily_prices_df = {}