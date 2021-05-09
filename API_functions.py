from packages import *
from config import *
from functions import *

## PRIVATE API FUNCTIONS
# KRAKEN 
def get_kraken_signature(urlpath, data, secret):
    postdata = urllib.parse.urlencode(data)
    encoded = (str(data['nonce']) + postdata).encode()
    message = urlpath.encode() + hashlib.sha256(encoded).digest()

    mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
    sigdigest = base64.b64encode(mac.digest())
    return sigdigest.decode()

def kraken_request(uri_path, data, api_key, api_sec):
    api_url = "https://api.kraken.com"

    if os.environ['ENCRYPT'] == 'True':
        api_key = decrypt(api_key)
        api_sec = decrypt(api_sec)

    headers = {}
    headers['API-Key'] = api_key
    headers['API-Sign'] = get_kraken_signature(uri_path, data, api_sec)             
    req = requests.post((api_url + uri_path), headers=headers, data=data)
    return req

## PUBLIC API FUNCTIONS
# KRAKEN
def fetch_OHLC_data(symbol, timeframe):
    """
    This function will get Open/High/Low/Close, Volume and tradecount data for the pair passed
    symbol must be in format XXX/XXX ie. BTC/USD
    """
    pair_split = symbol.split('/') 
    symbol = pair_split[0] + pair_split[1]
    url = f'https://api.kraken.com/0/public/OHLC?pair={symbol}&interval={timeframe}'
    response = requests.get(url)
    data=pd.DataFrame()
    if response.status_code == 200: 
        j = json.loads(response.text)
        result = j['result']
        keys = []
        for item in result:
            keys.append(item)
        if keys[0] != 'last':
            data = pd.DataFrame(result[keys[0]],columns=['unix', 'open', 'high', 'low', 'close', 'vwap', 'volume', 'tradecount'])
        else:
            data = pd.DataFrame(result[keys[1]],columns=['unix', 'open', 'high', 'low', 'close', 'vwap', 'volume', 'tradecount'])

        data['date'] = pd.to_datetime(data['unix'], unit='s')
        data['volume_from'] = data['volume'].astype(float) * data['close'].astype(float)

        if data is None:
            print("Did not return any data from Kraken for this symbol")
    else:
        print("Did not receieve OK response from Kraken API")
    return data

def fetch_SPREAD_data(symbol):
    """
    This function will return the nearest bid/ask and calculate the spread for the symbol passed
    symbol must be in format XXX/XXX ie. BTC/USD
    """
    pair_split = symbol.split('/') 
    symbol = pair_split[0] + pair_split[1]
    url = f'https://api.kraken.com/0/public/Spread?pair={symbol}'
    response = requests.get(url)
    data=pd.DataFrame()
    if response.status_code == 200: 
        j = json.loads(response.text)
        result = j['result']
        keys = []
        for item in result:
            keys.append(item)
        if keys[0] != 'last':
            data = pd.DataFrame(result[keys[0]], columns=['unix', 'bid', 'ask'])
        else:
            data = pd.DataFrame(result[keys[1]], columns=['unix', 'bid', 'ask'])

        data['date'] = pd.to_datetime(data['unix'], unit='s')
        data['spread'] = data['ask'].astype(float) - data['bid'].astype(float)

        if data is None:
            print("Did not return any data from Kraken for this symbol")
    else:
        print("Did not receieve OK response from Kraken API")
    return data