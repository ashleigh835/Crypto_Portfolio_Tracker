from packages import *
from config import *
from functions import *

## PRIVATE API FUNCTIONS
# COINBASE
class CoinbaseWalletAuth(AuthBase):
    """
    Create custom authentication for Coinbase API
    """
    def __init__(self, api_key, secret_key):
        self.api_key = api_key
        self.secret_key = secret_key

    def __call__(self, request):
        timestamp = str(int(time.time()))
        message = timestamp + request.method + request.path_url + (request.body or b'')
        signature = hmac.new(self.secret_key, message.encode(), hashlib.sha256).hexdigest()

        request.headers.update({
            'CB-ACCESS-SIGN': signature,
            'CB-ACCESS-TIMESTAMP': timestamp,
            'CB-ACCESS-KEY': self.api_key,
            'CB-VERSION': '2016-05-13'
        })
        return request

def coinbase_request(uri_path, data, api_key, api_sec):
    api_url = 'https://api.coinbase.com/v2/'
    
    if os.environ['ENCRYPT'] == 'True':
        api_key = decrypt(api_key)
        api_sec = decrypt(api_sec)
        
    auth = CoinbaseWalletAuth(api_key, api_sec)
    req = requests.get((api_url + uri_path),data=data,auth=auth)
    return req
        
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
def process_daily_price_data(response, exchange):
    """
    Process Daily Price Data Json Response
    Returns dataframe
    """
    data = pd.DataFrame()
    if exchange == 'kraken': 
        if 'result' in json.loads(response.text).keys():  
            keys=[]
            for item in json.loads(response.text)['result']:
                keys.append(item)
            if keys[0] != 'last':
                data = pd.DataFrame(json.loads(response.text)['result'][keys[0]],columns=['unix', 'open', 'high', 'low', 'close', 'vwap', 'volume', 'tradecount'])
            else:
                data = pd.DataFrame(json.loads(response.text)['result'][keys[1]],columns=['unix', 'open', 'high', 'low', 'close', 'vwap', 'volume', 'tradecount'])

            data['date'] = pd.to_datetime(data['unix'], unit='s')
            data['volume_from'] = data['volume'].astype(float) * data['close'].astype(float)
        else:
            print(f'bad response from {exchange} API')
            
    elif exchange == 'coinbase':
        data = pd.DataFrame(json.loads(response.text), columns=['unix', 'low', 'high', 'open', 'close', 'volume'])
        data['date'] = pd.to_datetime(data['unix'], unit='s')  
        data['volume_from'] = data['volume'].astype(float) * data['close'].astype(float)     

    else:
        print(f'Exchange: {exchange} not currently supported for daily prices')
    return data

def fetch_daily_price_individual(symbol, exchange):
    """
    This function will get Open/High/Low/Close, Volume and tradecount data for the pair passed
    symbol must be in format XXX/XXX ie. BTC/USD
    Only Kraken and Coinbase supported
    """    
    data=pd.DataFrame()
    pair_split = symbol.split('/')
    if exchange == 'kraken':
        symbol = pair_split[0] + pair_split[1]
        url = f'https://api.kraken.com/0/public/OHLC?pair={symbol}&interval=1440'
    elif exchange == 'coinbase':
        symbol = pair_split[0] + '-' + pair_split[1]
        url = f'https://api.pro.coinbase.com/products/{symbol}/candles?granularity=86400'
    else:
        print(f'Exchange: not currently supported for daily prices')
        return data
    response = requests.get(url)
    
    if response.status_code == 200: 
        data = process_daily_price_data(response, exchange)        
    else:
        print(f"Did not receieve OK response from {exchange} API for {symbol}")
    return data

def fetch_daily_price_pairs(pairs, exchange, dta=[]):
    """
    PULL DAILY PRICES FOR SPECIFIC PAIRS (This is a public API - doesn't need credentials)
    RETURNS A DATAFRAME AND A DICTIONARY WITH KEY: PAIR AND VALUE = DATAFRAME OF THE DAILY DATA
    """        
    daily_values_df = pd.DataFrame()
    for pair in pairs:
        if pair not in dta:
            print(f'new pair found! Pulling data for {pair}')
            tmp_dct = fetch_daily_price_individual(pair, exchange) 
            
            if tmp_dct.empty == False:
                tmpdf = tmp_dct.copy()[['date','high','low']]  
                tmpdf['high'] = tmpdf['high'].astype(float)
                tmpdf['low'] = tmpdf['low'].astype(float)
                tmpdf[pair] = (tmpdf['high']+tmpdf['low'])/2  

                tmpdf = tmpdf[['date',pair]].set_index('date')
                daily_values_df = pd.concat([daily_values_df,tmpdf], axis = 1, sort=True, join='outer')
                
                dta += [pair]
    
    return daily_values_df, dta

def kraken_fetch_SPREAD_data(symbol):
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

## DATA PROCESSING
def kraken_parse_api_results(resp, result_type):
    """
    Look at the results field of the API response.
    Result_type specifies the key within the response where the data lies.
    Returns as a dataframe
    """

    df = pd.DataFrame()
    if 'result' not in resp.json().keys():
        print(f"No result! Error: {resp.json()['error']}")
    else:
        for result in resp.json()['result'][result_type]:
            temp_df = pd.DataFrame(resp.json()['result'][result_type][result], index=[result])
            temp_df['time'] = pd.to_datetime(temp_df['time'], unit='s')
            temp_df['date'] = temp_df.time.dt.date.astype('datetime64')

            df = pd.concat([df,temp_df])
    return df

def coinbase_parse_api_results(resp):
    """
    Look at the data field of the API response.
    Includes logic to treat TRADES/BUYS/SENDS differently
    Returns as a dataframe
    """      

    df = pd.DataFrame()
    if 'data' not in resp.json().keys():
        print(f"No result! Error: {resp.json()['error']}")
    for data in resp.json()['data']:
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
                yy+=[data]     
                      
        elif data['type']== 'staking_reward':
            tmp['vol']=data['amount']['amount']
            tmp['cost']=0      

        else:
            print(f"type {data['type']} not supported!")
        
        tmp_df = pd.DataFrame(tmp, index=[data['id']])
        tmp_df['date'] = pd.to_datetime(tmp_df.created_at).dt.date.astype('datetime64')
        df = pd.concat([df, tmp_df], axis = 0, sort=False)
                
    return df