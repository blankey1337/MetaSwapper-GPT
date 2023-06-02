# blankey1337/MetaSwapper

MetaSwapper - Crypto Trading Bot Powered by MetaMask Swap API

This project was developed during the ConsenSys CypherPunk 2023 internal hackathon.
This is a proof of concept, use it at your own risk.
This bot is not ready for production use - it requires fine tuning and better memory management. By default, MetaSwapper is configured to trade on Polygon mainnet.

## Features

⚖️ Fetches balance using "get_balance" command

💹 Swaps tokens using "swap_tokens" command

♻️ Automatically selects the best route based on gas cost

💸 Can also send eth using "send_eth" command (disabled by default)


## What you'll need

1. A crypto wallet with funds in it. This must be a wallet you control (no exchange addresses). We will be adding your private key to the `.env` file in your auto-gpt installation. Note: This is not a seed phrase - do not use your seedphrase.
2. An Infura project. Infura accounts and projects are free at Infura.io. We will add your infura project ID to the `.env` file as well.

## Installation

1. Clone this repo as instructed in the main repository
2. Create an [Infura](https://infura.io) account and create a new web3 project.
3. Create a new MetaMask wallet address, fund it, and copy the private key to your clipboard.
4. Configure the env vars by adding and editing these lines to the `.env` file within AutoGPT:

```
ETH_PRIVATE_KEY=[your private key exported from MetaMask (NOT your seedphrase)]
ETH_INFURA_PROJECT_ID=[your infura project id]
```
