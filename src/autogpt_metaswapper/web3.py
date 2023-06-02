"""This module contains functions for trading crypto via MetaMask APIs"""
from __future__ import annotations

import os
from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware
from eth_account import Account
from autogpt.config import Config
import urllib
from decimal import Decimal
import requests
import json

from . import AutoGPTMetaSwapper

plugin = AutoGPTMetaSwapper()


infura_project_id = os.getenv("ETH_INFURA_PROJECT_ID")

## Sepolia Testnet
# INFURA_URL = f"https://sepolia.infura.io/v3/{infura_project_id}"

## Mainnet
# INFURA_URL = f"https://mainnet.infura.io/v3/{infura_project_id}"

## Polygon
INFURA_URL = f"https://polygon-mainnet.infura.io/v3/{infura_project_id}"


# Connect to Ethereum node
w3 = Web3(HTTPProvider(INFURA_URL))

account = Account.from_key(os.getenv("ETH_PRIVATE_KEY"))
address = Web3.to_checksum_address(account.address)

network_config = {
    'gas_type': 'Traditional'
}

def send_eth(to_address: str, amount: int) -> str:
    """Send ETH on the Ethereum network

    Args:
        to_address (str): The address to receive the ETH
        amount (str): The amount to send in ETH

    Returns:
        str: Success or failure message
    """

    # Build the transaction
    transaction = {
        'to': to_address,
        'value': w3.to_wei(amount, 'ether'),
        'gas': 21000,
        'gasPrice': w3.eth.gas_price,
        'nonce': w3.eth.get_transaction_count(address),
        'chainId': w3.eth.chain_id
        # 'chainId': 11155111, # sepolia
    }

    # Sign the transaction
    signed_transaction = account.sign_transaction(transaction)

    # Send the transaction and get the transaction hash
    transaction_hash = w3.eth.send_raw_transaction(signed_transaction.rawTransaction)
    print(f"Transaction hash: {transaction_hash.hex()}")

    # Wait for the transaction receipt
    transaction_receipt = w3.eth.wait_for_transaction_receipt(transaction_hash)
    return f"Transaction success. Receipt: {transaction_receipt}"

def get_balance():
    """Check the balance of the account

    Returns:
        str: Current balance
    """

    url = 'https://account.metafi.codefi.network/accounts/' + address
    params = {'chainId': w3.eth.chain_id, 'includePrices': 'true'}
    headers = {
        'authority': 'account.metafi.codefi.network',
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'no-cache',
        'origin': 'https://portfolio.metamask.io',
        'pragma': 'no-cache',
        'referer': 'https://portfolio.metamask.io/',
        'sec-ch-ua': '"Chromium";v="112", "Brave";v="112", "Not:A-Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'cross-site',
        'sec-gpc': '1',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'
    }

    response = requests.get(url, params=params, headers=headers)

    formatted_output = format_token_balances(json.loads(response.content))

    return f"Current account balance: {formatted_output}"


def swap_tokens(source_amount: str, source_token: str, destination_token: str, wallet_address: str = address, slippage: int = 2) -> str:
    """Swaps crypto tokens on any EVM-compatible network

    Args:
        source_amount (str): 1
        source_token (str): source token address
        destination_token (str): dest token address

    Returns:
        str: Success or failure message
    """

    # if source_amount > w3.from_wei(w3.eth.get_balance(address)):
    #     return 'Error: not enough tokens'
    
    # MetaMask swaps URL
    SWAP_API_URL = 'https://swap.metaswap.codefi.network/networks/' + str(w3.eth.chain_id) + '/trades?' + urllib.parse.urlencode({
        'sourceAmount': w3.to_wei(source_amount, 'ether'),
        'sourceToken': source_token,
        'destinationToken': destination_token,
        'slippage': 2,
        'walletAddress': wallet_address,
        'timeout': 10000,
        'enableDirectWrapping': "true",
        'includeRoute': "true"
    })

    response = requests.get(SWAP_API_URL)

    if "trade" in str(response.content):

        # Sign the transaction
        tx = handle_api_response(response.content)
        
        signed_transaction = account.sign_transaction(tx)

        # Send the transaction and get the transaction hash
        transaction_hash = w3.eth.send_raw_transaction(signed_transaction.rawTransaction)

        # Wait for the transaction receipt
        transaction_receipt = w3.eth.wait_for_transaction_receipt(transaction_hash)
        return f"Transaction success. Tx hash: {transaction_hash.hex()}"

    else:
        return "Error: swap failed"


def handle_api_response(response):

    GAS_PRICE_URL = 'https://gas.metaswap.codefi.network/networks/' + str(w3.eth.chain_id) + '/suggestedGasFees'

    gas_prices_response = requests.get(GAS_PRICE_URL)
    gas_prices = json.loads(gas_prices_response.content)

    json_data = json.loads(response)
    trade_data = None
    min_gas_cost = None

    for entry in json_data:
        if entry.get("trade") is not None:
            current_trade_data = entry
            gas_estimates = get_gas_estimates_for_quote(current_trade_data, gas_prices)
            current_gas_cost = Decimal(gas_estimates['maxGas'])

            if min_gas_cost is None or current_gas_cost < min_gas_cost:
                min_gas_cost = current_gas_cost
                trade_data = current_trade_data["trade"]

    if trade_data is None:
        print("No trades found.")
        return {}

    trade_details = {
        "chainId": w3.eth.chain_id,
        "data": trade_data["data"],
        "from": Web3.to_checksum_address(trade_data["from"]),
        "value": w3.to_wei(trade_data["value"], 'wei'),
        "to": trade_data["to"],
        'gas': w3.to_wei(current_trade_data.get('maxGas'), 'wei'),
        'gasPrice': w3.to_wei(Decimal(gas_prices['estimatedBaseFee']) + Decimal(gas_prices['medium']['suggestedMaxPriorityFeePerGas']), 'gwei'),
        'nonce': w3.eth.get_transaction_count(address),
    }

    return trade_details


def get_gas_estimates_for_quote(quote, gas_prices):

    estimated_gas_fee = (
        Decimal(gas_prices['estimatedBaseFee']) + Decimal(gas_prices['medium']['suggestedMaxPriorityFeePerGas'])
    )

    estimated_gas = (
        Decimal(quote.get('averageGas', 0))
        * estimated_gas_fee
        * Decimal(quote.get('gasMultiplier', 0))
    )

    estimated_gas_eth = estimated_gas / (10 ** 9)

    max_gas = (
        Decimal(quote.get('maxGas', 0))
        * Decimal(gas_prices['medium']['suggestedMaxFeePerGas'])
    )

    max_gas_eth = (max_gas / (10 ** 9)).quantize(Decimal('.0001'))

    return {
        'maxGas': str(max_gas),
        'maxGasEth': str(max_gas_eth),
        'estimatedGasEth': str(estimated_gas_eth)
    }

def format_token_balances(data):
    native_balance = data["nativeBalance"]
    token_balances = data["tokenBalances"]

    result = f"Account Address: {data['accountAddress']}\n\n"

    result += f"{native_balance['symbol']} ({native_balance['name']}): {native_balance['balance']} {native_balance['symbol']}\n"
    result += f"Token Address: {native_balance['address']}\n"
    result += f"Value (USD): {native_balance['value']['marketValue']}\n\n"

    for token in token_balances:
        result += f"{token['symbol']} ({token['name']}): {token['balance']} {token['symbol']}\n"
        result += f"Token Address: {token['address']}\n"
        result += f"Value (USD): {token['value']['marketValue']}\n\n"

    return result


