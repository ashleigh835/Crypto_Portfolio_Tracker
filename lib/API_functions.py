from config import infura_key

import requests
import json

def blockchain_address_api(addresses):
    """
    uses the blockchain.info api to query the current balance for bitcoin addresses

    Args:
        addresses ([str]): list of bitcoin addresses

    Returns:
        dict: json result from API
    """
    address_str =''
    for address in addresses:
        address_str = '|'.join(addresses)
    url = f'https://blockchain.info/balance?active={address_str}'
    response = requests.get(url)
    if response.status_code == 200: 
        return json.loads(response.text)      
    else:
        print(f"Did not receieve OK response from {address}. Received: {response.status_code}")

def infura_eth_address(addresses, infura_key=infura_key):
    """
    uses the web3 package and infura provider to query the current balance for ethereum addresses

    Args:
        addresses ([str]): list of ethereum addresses

    Returns:
        dict: json result from API
    """
    from web3 import Web3
    w3 = Web3(Web3.HTTPProvider(f'https://mainnet.infura.io/v3/{infura_key}'))
    address_dict = {}
    for address in addresses:
        address_dict[address] = {'final_balance' : w3.fromWei(w3.eth.get_balance(address),'ether')}
    return address_dict

def coinexplorer_addresses_api(asset, addresses):
    """
    uses the coin explorer API to retrieve prices for specific assets (only VTC supported right now)

    Args:
        asset (str): asset to look up balance for (only VTC supported right now)
        addresses ([str]): wallet address to query balance for

    Returns:
        dict: dictionary of balances for the asset and addresses provided
    """
    address_dict = {}
    if asset != 'VTC': 
        print(f"asset not supported for coinexplorer")
        return address_dict

    api_url = 'https://www.coinexplorer.net/api/v1'
    for address in addresses:
        uri_path = f'/{asset}/address/balance?address={address}'
        response = requests.get(f'{api_url}{uri_path}')
        if response.status_code == 200: 
            if ('success' in response.json().keys()) & ('result' in response.json().keys()):
                address_dict[address] = {'final_balance' : response.json()['result'][address]}
            elif ('error' in response.json().keys()) & (response.json()['error'] is not None):
                for err in response.json()['error']:
                    print(f"error: {err}")
        else:
            print(f"Did not receieve OK response from {address}. Received: {response.status_code}")  
            print(response.json())
    return address_dict