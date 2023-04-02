import time
from web3 import Web3
import requests
import json
from telegram import Bot, Update
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater

# Replace YOUR_BOT_TOKEN with your actual bot token
TELEGRAM_BOT_TOKEN = "5867891698:AAE9u5AwPg-R6Gmt27kboU1lvwwgR0McI4U"

# Set your BNB private key
BNB_PRIVATE_KEY = "fc8d65548ab80e4506e2316b4f1beda32c6b169219224f9b7660df7b875fc094"

# Set your BNB address
BNB_ADDRESS = "0xA1abB5177Cb14B2B99C362157337CE7E0A695630"

# SRG20 contract address
SRG20_CONTRACT_ADDRESS = "0x253af03a3b6e1a6d9d9bb6535834f8993221fb9b"

# Surge contract address and ABI
SURGE_CONTRACT_ADDRESS = "0x9f19c8e321bd14345b797d43e01f0eed030f5bff"
SURGE_ABI_URL = "https://api.bscscan.com/api?module=contract&action=getabi&address=0x9f19c8e321bd14345b797d43e01f0eed030f5bff&apikey=8R67G1EHCA6QCJ3Y2X3YMWPTUMD25ZYH4Z"

# Web3 provider
WEB3_PROVIDER = "https://bsc-dataseed.binance.org/"

# Initialize web3
w3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER))

# Get Surge ABI
response = requests.get(SURGE_ABI_URL)
surge_abi = json.loads(response.text)["result"]

# Initialize the Surge contract
surge_contract = w3.eth.contract(
    address=Web3.to_checksum_address(SURGE_CONTRACT_ADDRESS),
    abi=surge_abi,
)

# Initialize the Telegram bot
bot = Bot(token=TELEGRAM_BOT_TOKEN)
updater = Updater(token=TELEGRAM_BOT_TOKEN)

# Set auto-buy status
auto_buy_status = False

def get_token_decimals(contract_address):
    token_abi_url = f"https://api.bscscan.com/api?module=contract&action=getabi&address={contract_address}&apikey=8R67G1EHCA6QCJ3Y2X3YMWPTUMD25ZYH4Z"
    response = requests.get(token_abi_url)
    token_abi = json.loads(response.text)["result"]

    token_contract = w3.eth.contract(
        address=Web3.to_checksum_address(contract_address),
        abi=token_abi,
    )

    return token_contract.functions.decimals().call()



def start_auto_buy(update: Update, context):
    global auto_buy_status
    auto_buy_status = True
    update.message.reply_text("Auto-buy started.")
    surge_decimals = get_token_decimals("0x9f19c8e321bd14345b797d43e01f0eed030f5bff")
    buy_srg20_with_surge(update, 0.1, 10, Web3.to_checksum_address("0x9f19c8e321bd14345b797d43e01f0eed030f5bff"), surge_decimals)

def stop_auto_buy(update: Update, context):
    global auto_buy_status
    auto_buy_status = False
    update.message.reply_text("Auto-buy stopped.")

def approve_surge_transfer(surge_amount, surge_decimals):
    # Build the approve transaction
    approve_data = surge_contract.encodeABI(
        fn_name="approve",
        args=[
            Web3.to_checksum_address(SRG20_CONTRACT_ADDRESS),
            Web3.to_wei(surge_amount, 'ether'),
        ],
    )

    approve_dict = {
        'from': Web3.to_checksum_address(BNB_ADDRESS),
        'gas': 2500000,
        'gasPrice': w3.eth.gas_price,
        'nonce': w3.eth.get_transaction_count(Web3.to_checksum_address(BNB_ADDRESS)),
        'to': Web3.to_checksum_address(SURGE_CONTRACT_ADDRESS),
        'value': 0,
        'data': approve_data
    }

    # Build and sign the approve transaction
    signed_approve_txn = w3.eth.account.sign_transaction(approve_dict, BNB_PRIVATE_KEY)

    # Send the approve transaction
    approve_hash = w3.eth.send_raw_transaction(signed_approve_txn.rawTransaction)
    approve_receipt = w3.eth.wait_for_transaction_receipt(approve_hash)
    return approve_receipt

def buy_srg20_with_surge(update, surge_amount, time_interval, surge_contract_address, surge_decimals):

    global auto_buy_status

    while auto_buy_status:
        # Check balance of Surge token
        surge_balance = surge_contract.functions.balanceOf(Web3.to_checksum_address(BNB_ADDRESS)).call()
        if surge_balance / (10 ** surge_decimals) < surge_amount:
            update.message.reply_text(f"Insufficient balance of Surge token ({surge_balance / (10 ** surge_decimals)} < {surge_amount}). Auto-buy stopped.")
            auto_buy_status = False
            break

        # Get the current block timestamp and set a deadline
        current_block = w3.eth.get_block('latest')
        current_timestamp = current_block['timestamp']
        deadline = current_timestamp + 120  # Deadline in 2 minutes

        # Build the transaction
        transaction_data = surge_contract.encodeABI(
            fn_name="_buy",
            args=[
                w3.to_wei(surge_amount, "ether"),
                deadline,
            ],
        )

        transaction_dict = {
            'from': Web3.to_checksum_address(BNB_ADDRESS),
            'gas': 2500000,
            'gasPrice': w3.eth.gas_price,
            'nonce': w3.eth.get_transaction_count(Web3.to_checksum_address(BNB_ADDRESS)),
            'to': Web3.to_checksum_address(SURGE_CONTRACT_ADDRESS),
            'value': w3.to_wei(surge_amount, "ether"),
            'data': transaction_data
        }

        # Build and sign the transaction
        signed_txn = w3.eth.account.sign_transaction(transaction_dict, BNB_PRIVATE_KEY)

        try:
            # Send the transaction
            txn_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            txn_receipt = w3.eth.wait_for_transaction_receipt(txn_hash)

            if txn_receipt["status"]:
                update.message.reply_text(f"Transaction successful: {txn_hash.hex()}")
            else:
                update.message.reply_text(f"Transaction failed: {txn_hash.hex()}")
        except Exception as e:
            update.message.reply_text(f"Error: {str(e)}")

        time.sleep(time_interval * 60)




start_auto_buy_handler = CommandHandler("start", start_auto_buy)
stop_auto_buy_handler = CommandHandler("stop", stop_auto_buy)

updater.dispatcher.add_handler(start_auto_buy_handler)
updater.dispatcher.add_handler(stop_auto_buy_handler)

updater.start_polling()
updater.idle()

