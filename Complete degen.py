import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import re
import time
import asyncio
from openapi_evm_api.exceptions import ApiException
from datetime import datetime
from queue import Queue
import aiohttp
import random
import telegram
from telegram.ext import Updater, CommandHandler
import threading
from aiohttp import ClientSession
from telegram.ext import CallbackContext
from telegram import Bot
import os
import emoji
from telegram import Update, ParseMode
from telegram.ext import CommandHandler, CallbackContext
from moralis import evm_api
from dateutil.parser import parse
import httpx

API_KEY = "7AVTSE6MXU118P2I7FZTMHD2UD6PU71RQF"
WALLET_CHECK_INTERVAL = 5  # Check for new wallets every 60 seconds






with open('transaction_actions.txt', 'a', encoding='utf-8', errors='ignore') as f:
        pass
user_wallets_in_queue = {}
wallet_queue = Queue()
def delete_wallet_addresses():
    while True:
        time.sleep(60)  # wait for 5 minutes
        with open("wallet_addresses.txt", 'a', encoding='utf-8', errors='ignore') as f:
            f.write("")  # write an empty string to clear the file
async def process_transaction_actions(chat_id, message_id):
    token_lines = {}
    token_eth_values = {}
    total_eth_buys = 0.0
    total_eth_sells = 0.0
    win_loss = {}
    win_count = 0
    loss_count = 0
    token_groups = 0
    holding_tokens_value = 0.0
    token_addresses = {}
    total_token_value_in_eth = 0
    def extract_token_address(line):
        token_address = re.search(r'/token/(.*?)\s', line)
        return token_address.group(1) if token_address else None


    with open('transaction_actions.txt', 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            if 'Transaction Action:Swap' in line:
                if "OnUniswap" in line:
                    traded_token_index = line.find("OnUniswap") - 1
                elif "For" in line:
                    traded_token_index = line.find("For") - 1
                else:
                    continue


                traded_token = ""
                if "For" in line:
                    for i in range(traded_token_index, -1, -1):
                        if not line[i].isnumeric() and line[i] != ".":
                            traded_token = line[i] + traded_token
                        else:
                            break
                    if traded_token == "Ether":
                        traded_token_index = line.find("For") - 1
                        for i in range(traded_token_index, -1, -1):
                            if not line[i].isnumeric() and line[i] != ".":
                                traded_token = line[i] + traded_token
                            else:
                                break
                elif "OnUniswap" in line:
                    traded_token = line[line.find(" ")+1:traded_token_index+1]
                else:
                    continue


                eth_value = ""
                if "Ether" in line:
                    eth_value_index = line.find("Ether") - 1
                    for i in range(eth_value_index, -1, -1):
                        if line[i].isnumeric() or line[i] == ".":
                            eth_value = line[i] + eth_value
                        elif line[i] == ",":
                            continue
                        else:
                            break


                if traded_token not in token_lines:
                    token_lines[traded_token] = []
                    token_eth_values[traded_token] = 0.0
                    token_groups += 1
                    token_address = extract_token_address(line)
                if token_address:
                    token_addresses[traded_token] = token_address
                token_lines[traded_token].append(line)
                if eth_value:
                    token_eth_values[traded_token] += float(eth_value)


                if "Ether" not in traded_token and "OnUniswap" in line:
                    if eth_value.strip():
                        total_eth_buys += float(eth_value)
                elif "Ether" in traded_token and "For" in line:
                    total_eth_sells += float(eth_value)




    with open('unique_token_lines.txt', 'a', encoding='utf-8', errors='ignore') as f:
        f.write(f"Total ETH Buys: {total_eth_buys:.8f}\n")
        f.write(f"Total ETH Sells: {total_eth_sells:.8f}\n\n")
        for token in sorted(token_lines.keys()):
            token_address = token_addresses.get(token, '')
            group_name = f"Token: {token} ({token_address}) - ETH Value: {token_eth_values[token]:.8f}"
            f.write(group_name + "\n")
            for line in token_lines[token]:
                f.write(line)
        for token in sorted(token_lines.keys()):
            if "Ether" not in token and f"{token}Ether" in token_eth_values:
                win_loss[token] = token_eth_values[f"{token}Ether"] - token_eth_values[token]
                result = "Win" if win_loss[token] > 0 else "Loss"
                if result == "Win":
                    win_count += 1
                else:
                    loss_count += 1
                f.write(f"{result} for {token}: {win_loss[token]:.8f}\n")
            elif "Ether" not in token and f"{token}Ether" not in token_eth_values:
                f.write(f"Tokens Still Holding {token}: {token_eth_values[token]:.8f}\n")
                holding_tokens_value += token_eth_values[token]
                loss_count += 1
            f.write(f"Token: {token} - ETH Value: {token_eth_values[token]:.8f}\n")
            for line in token_lines[token]:
                f.write(line)




        f.write(f"\nTotal token groups: {token_groups}\n")
        f.write(f"Total Wins: {win_count}\n")
        f.write(f"Total Losses: {loss_count}\n")
        f.write(f"Tokens Still Holding Value: {holding_tokens_value:.8f}\n")


    print(f'Wrote {sum(len(lines) for lines in token_lines.values())} unique token lines to unique_token_lines.txt')
    win_loss_count = win_count + loss_count
    if win_loss_count > 0:
        win_percentage = win_count / win_loss_count * 100
    else:
        win_percentage = 0.0
    with open('summary.txt', 'a', encoding='utf-8', errors='ignore') as f:
        f.write(f"Total ETH Buys: {total_eth_buys:.8f}\n")
        f.write(f"Total ETH Sells: {total_eth_sells:.8f}\n")
        f.write(f"Total Wins: {win_count}\n")
        f.write(f"Total Losses: {loss_count}\n")
        f.write(f"Win Percentage: {win_percentage:.2f}%\n")
        f.write(f"Tokens Still Holding Buy Value: {holding_tokens_value:.8f}\n")
    with open('unique_token_lines.txt', 'a', encoding='utf-8', errors='ignore') as f:
        f.write(f"\nTotal Wins: {win_count}\n")
        f.write(f"Total Losses: {loss_count}\n")
        f.write(f"Win Percentage: {win_percentage:.2f}%\n")
    
    with open('unique_token_lines.txt', 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()


        for i in range(len(lines)):
            if lines[i].startswith('Token:'):
        # Find the token address on the next line
                for j in range(i+1, len(lines)):
                    if ' ' in lines[j].strip():
                        token_address = lines[j].strip().split()[-1]
                # Add token address to the existing line
                        lines[i] = lines[i].rstrip() + f" {token_address}\n"
                        break


    with open('unique_token_lines.txt', 'w', encoding='utf-8', errors='ignore') as f:


        f.writelines(lines)
        
    api_key = "D1SbGvTf6B5tO2KTM953y3l0JjDoClAATqUfHa7KdZ3CFclJFTytXePps8IpKndt"


# Get wallet address from the last line in tempwallet.txt
    with open('tempwallet.txt', 'r') as f:
        wallet_address = f.readlines()[-1].strip()


    print(f"Wallet address: {wallet_address}")


    balance_params = {
        "chain": "eth",
        "address": wallet_address
    }


# WETH contract address
    weth_address = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"


# Get ETH price in USD using the WETH contract address
    eth_price_params = {
        "chain": "eth",
        "exchange": "uniswap-v2",
        "address": weth_address
    }


    eth_price_result = evm_api.token.get_token_price(api_key=api_key, params=eth_price_params)


    print(f"ETH price result: {eth_price_result}")


# Access the quote value to get the ETH price in USD
    eth_usd_price = eth_price_result['usdPrice'] if eth_price_result else None


    print(f"ETH USD price: {eth_usd_price}")


    with open('unique_token_lines.txt', 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()


        processed_token_addresses = set()
        updated_lines = []


        last_transaction_time = None


        for line in lines:
            if line.startswith('Token:'):
                token_address = line.strip().split()[-1]


            # Check if the token_address is already processed
                if token_address in processed_token_addresses:
                    print(f"Skipping duplicate token address: {token_address}")
                    updated_lines.append(line)
                    continue


            # Process the token address
                print(f"Token address: {token_address}")


            # Add the token_address to the set of processed addresses
                processed_token_addresses.add(token_address)


            # Get the time of the last transaction for the token_address
                params = {
                    "chain": "eth",
                    "contract_addresses": [token_address],
                    "limit": 1
                }


                result = evm_api.token.get_erc20_transfers(
                    api_key=api_key,
                    params=params,
                )
                print(f"Token Transfers Results: {result}")


                block_timestamp_str = result['result'][0]['block_timestamp']
                block_timestamp = datetime.fromisoformat(block_timestamp_str.replace('Z', ''))
                current_datetime = datetime.utcnow()
                days_difference = (current_datetime - block_timestamp).days


                if days_difference > 2:
                    print(f"Skipping token address {token_address} because the last transaction was more than 2 days ago.")
                    updated_lines.append(line)
                    continue


                balance_params["token_addresses"] = (token_address,)
                balance_result = evm_api.token.get_wallet_token_balances(api_key=api_key, params=balance_params)


                if len(balance_result) > 0:
                    token_decimals = balance_result[0].get('decimals', 18)
                    token_raw_balance = float(balance_result[0]['balance'])
                    token_balance = token_raw_balance / (10 ** token_decimals)
                else:
                    token_balance = 0


                print(f"Token balance: {token_balance}")


                token_price_params = {"chain": "eth", "address": token_address}
                try:
                    token_price_result = evm_api.token.get_token_price(api_key=api_key, params=token_price_params)
                except ApiException as e:
                    print(f"Error getting token price: {e}")
                    return


                token_price_result = evm_api.token.get_token_price(api_key=api_key, params=token_price_params)
                token_eth_price = token_price_result.get('nativePrice', {}).get('value') if token_price_result else 0
                token_eth_price = float(token_eth_price) / (10 ** token_price_result.get('nativePrice', {}).get('decimals', 18))


                if token_eth_price > 0.25:
                    token_eth_price = 0


                print(f"Token ETH price: {token_eth_price}")


                token_value_in_eth = token_balance * token_eth_price
                token_value_in_eth = token_balance * token_eth_price
                if token_value_in_eth < 0.001:
                    token_value_in_eth = 0


                total_token_value_in_eth += token_value_in_eth
                if token_value_in_eth > 0:
                    line = line.rstrip() + f" Value: {token_value_in_eth} ETH\n"


            # Add token value in ETH to the existing line
                line = line.rstrip()[:-1] + f" Value: {token_value_in_eth} ETH\n"


            updated_lines.append(line)


    # Write the updated lines to the file
        with open('unique_token_lines.txt', 'w', encoding='utf-8', errors='ignore') as f:
            f.writelines(updated_lines)


    print("Finished updating unique_token_lines.txt")





    
    bot_token = "6199122710:AAGp9NZijxj1F4_4PeAp0fjUZU7aY_MZ4qs"
    bot = telegram.Bot(token=bot_token)
    chart_link = 'https://www.dextools.io/app/en/ether/pair-explorer/0xa2376a5304cfcd238f52db5677cba3e0559f7f09'
    bot_name = '🤖 WALLY BOT ANALYSIS 🤖'
    message = f'{bot_name}\n'
    message += '—————————————--\n'
    message += f'💵 Total Buys: {total_eth_buys:.8f}e\n'
    message += f'💰 Total Sells: {total_eth_sells:.8f}e\n'
    message += '—————————————--\n'
    message += f'✅ Total Wins: {win_count}\n'
    message += f'❌ Total Losses: {loss_count}\n'
    message += f'💯 Win Percentage: {win_percentage:.2f}%\n'
    message += '—————————————--\n'
    message += f'☑️ Buy Price: {holding_tokens_value:.8f}e\n'
    message += '=========================\n'
    message += '@WallyBot_Group'

    await asyncio.to_thread(bot.send_message, chat_id=chat_id, text=message, reply_to_message_id=message_id)


   
async def fetch_etherscan_transaction_page(tx_hash):
    base_url = 'https://etherscan.io/tx/'
    url = base_url + tx_hash


    # Use the ScrapeOps API key and endpoint
    api_key = '7c63d044-84fe-4c3f-b0c6-09f122b5e3d6'
    scrapeops_url = 'https://proxy.scrapeops.io/v1/'


    while True:
        async with aiohttp.ClientSession(trust_env=True) as session:
            async with session.get(scrapeops_url, params={"api_key": api_key, "url": url}, ssl=False) as response:
                if response.status == 200:
                    html = await response.text()
                    if "No transactions found for this address" in html:
                        print("No transactions found for this address.")
                        process_transaction_actions()
                        return None
                    else:
                        return html
                else:
                    print(f'Request failed with status code {response.status}. Retrying...')
                    await asyncio.sleep(random.randint(1, 5))








def extract_transaction_action_and_token_address(tx_page):
    match = re.search(r'Transaction Action[\s\S]*?\<\/td\>', tx_page)


    transaction_action_text = None
    token_address = None


    if match:
        transaction_action_html = match.group()
        soup = BeautifulSoup(transaction_action_html, 'html.parser')
        transaction_action_text = soup.get_text(strip=True).splitlines()[0]


        token_address_match = re.search(r'\/token\/(0x[a-fA-F0-9]{40})', tx_page)
        if token_address_match:
            token_address = token_address_match.group(1)


    return transaction_action_text, token_address


def write_transaction_action_to_file(tx_hash, transaction_action, token_address, filename):
    with open(filename, 'a', encoding='utf-8') as f:
        f.write(f"{tx_hash}\t{transaction_action}\t{token_address}\n")
        


def wallet_handler(update, context):
    user_input = update.message.text.split()
    if len(user_input) != 2:
        update.message.reply_text("Please use the correct format: /wallet WALLET_ADDRESS")
        return


    wallet_address = user_input[1]
    chat_id = update.message.chat_id


    # Check for duplicate addresses in the text file
    with open("wallet_addresses.txt", "r", encoding="utf-8", errors="ignore") as f:
        existing_addresses = f.read().splitlines()
    if wallet_address in existing_addresses:
        update.message.reply_text(f"The wallet address {wallet_address} is already being processed.")
        return


    # Add the new address to the text file
    with open("wallet_addresses.txt", "a", encoding="utf-8") as f:
        f.write(f"{wallet_address}\n")
    with open("Summary.txt", "a", encoding="utf-8") as f:
        f.write(f"{wallet_address}\n")
    with open("tempwallet.txt", "a", encoding="utf-8") as f:
        f.write(f"{wallet_address}\n")


    # Queue the new address for processing
    asyncio.run(wallet(update, context, wallet_address, chat_id))






async def wallet(update, context, wallet_address, chat_id=None):
    if os.path.exists("unique_token_lines.txt"):
        os.remove("unique_token_lines.txt")

    # Delete transaction_actions.txt if it exists
    if os.path.exists("transaction_actions.txt"):
        os.remove("transaction_actions.txt")

    url = f"https://api.etherscan.io/api?module=account&action=txlist&address={wallet_address}&apikey={API_KEY}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response_json = response.json()
    
    # Add the code snippet to get ETH balance
    eth_balance_url = f"https://api.etherscan.io/api?module=account&action=balance&address={wallet_address}&apikey={API_KEY}"
    async with httpx.AsyncClient() as client:
        response = await client.get(eth_balance_url)
        eth_balance_json = response.json()
    eth_balance = int(eth_balance_json["result"]) / 10**18

    
    transaction_hashes = []  # Initialize an empty list for transaction_hashes


    if response_json["message"] == "OK":
        transaction_hashes = [tx["hash"] for tx in response_json["result"]]


        # Check if the wallet has more than 4000 transactions
        if len(transaction_hashes) > 1500:
            await asyncio.to_thread(
                bot.send_message,
                chat_id=chat_id,
                text="We do not process wallets with over 1500 transactions At this time.",
                reply_to_message_id=update.message.message_id,
            )
            return asyncio.sleep(0)  # Stop processing the wallet


        # Create an empty 'transaction_actions.txt' file if it doesn't exist
        if not os.path.exists('transaction_actions.txt'):
            with open('transaction_actions.txt', 'w') as f:
                pass


        output_file = 'transaction_actions.txt'


        semaphore = asyncio.Semaphore(200)
        html_queue = asyncio.Queue()


        async def process_transaction(tx_hash):
            async with semaphore:
                print(f"Fetching transaction hash {tx_hash}")
                tx_page = await fetch_etherscan_transaction_page(tx_hash)


                if tx_page:
                    await html_queue.put((tx_hash, tx_page))


        async def process_html():
            while True:
                tx_hash, tx_page = await html_queue.get()


                transaction_action, token_address = extract_transaction_action_and_token_address(tx_page)
                if transaction_action and token_address:
                    write_transaction_action_to_file(tx_hash, transaction_action, token_address, output_file)
                    print(f"Transaction action and token address for {tx_hash} have been saved to {output_file}")
                else:
                    print(f"Transaction action or token address not found for {tx_hash}")


                html_queue.task_done()


        num_workers = 3000
        workers = [asyncio.create_task(process_html()) for _ in range(num_workers)]


        tasks = [process_transaction(tx_hash) for tx_hash in transaction_hashes]
        await asyncio.gather(*tasks)


        await html_queue.join()


        for worker in workers:
            worker.cancel()


    if not transaction_hashes:
        message = f"No transactions found for {wallet_address}"
        await asyncio.to_thread(bot.send_message, chat_id=chat_id, text=message, reply_to_message_id=update.message.message_id)
    else:
       await process_transaction_actions(chat_id, update.message.message_id)


  # Pass the chat_id here

async def process_wallet_queue():
    while True:
        if not wallet_queue.empty():
            wallet_address, chat_id = wallet_queue.get()

            await wallet(None, None, wallet_address, chat_id)

        await asyncio.sleep(WALLET_CHECK_INTERVAL)



async def fetch_transactions(wallet_address, api_key):
    transactions = await fetch_wallet_transactions(wallet_address, api_key)
    total_transactions = len(transactions)
    print(f'Total transactions: {total_transactions}')


    tasks = []
    processed_counter = 0


    for tx_hash in transactions:
        print(f"Fetching transaction hash {tx_hash}")
        task = asyncio.ensure_future(fetch_etherscan_transaction_page(tx_hash, api_key))
        tasks.append(task)


    transaction_actions = {}


    for task in asyncio.as_completed(tasks):
        tx_page = await task


        if tx_page:
            transaction_action = extract_transaction_action(tx_page)


            if transaction_action:
                tx_hash = extract_transaction_hash(tx_page)
                transaction_actions[tx_hash] = transaction_action
                processed_counter += 1


        if processed_counter == total_transactions:
            process_transaction_actions(transaction_actions)


async def main_async():
    # Replace YOUR_TELEGRAM_BOT_TOKEN with your actual bot token
    bot_token = "6199122710:AAGp9NZijxj1F4_4PeAp0fjUZU7aY_MZ4qs"
    updater = Updater(bot_token, use_context=True)


    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher


    # Add the wallet command handler
    wallet_command_handler = CommandHandler("wallet", wallet_handler)


    dispatcher.add_handler(wallet_command_handler)
    # Add the wallet command handler
    wallet_command_handler = CommandHandler("wallet", wallet_handler)
    dispatcher.add_handler(wallet_command_handler)


    # Start the bot
    updater.start_polling()


    # Start the wallet processing loop
    await process_wallet_queue()


    # Block until the user presses Ctrl-C or the process receives SIGINT, SIGTERM or SIGABRT
    updater.idle()


def main():
    asyncio.run(main_async())


if __name__ == '__main__':
    main()