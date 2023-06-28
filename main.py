import asyncio
import os

import matplotlib.pyplot as plt
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import aiohttp
import traceback

# Binance API credentials
API_KEY = 'Q2CP4LlaXcnMYgVQsuCUhFfkPSeT2T0xAxnAXVYAUkcqQUMIQ8y5PH5kFKvjiqEt'
API_SECRET = 'cyVrJ14a5JSlzvG7qdkx8fKiPOsFEwjF5ZEoqRPrd0XWLWOj9yPUTujsyvI3Q7u7'
exchange_rate_api = 'https://api.exchangerate-api.com/v4/latest/USD'
coin_gecko_base_url = 'https://api.coingecko.com/api/v3'




# Create a bot instance
bot = Bot(token='6035529879:AAGEmTSQHMmptoE-F9rWVjgohsYBAqn6Ryg')

# Create a dispatcher instance
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

user_thresholds = {}


# Command handler for /start
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.answer("Добро пожаловать в криптовалютный бот!\n"
                         "Введите /help чтобы посмотреть основные команды")

# Command handler for /help
@dp.message_handler(commands=['help'])
async def cmd_help(message: types.Message):
    await message.answer("/rates - получить цены на все криптовалюты.\n"
                         "/threshold [cryptocurrency] [threshold_value] - установка уведомления о пороге цены.\n"
                         "/btc - получить текущую цену Bitcoin.\n"
                         "/eth - получить текущую цену Ethereum.\n"
                         "/usdt - получить текущую цену USDT. \n"
                         "/rate [cryptocurrency] - получить цену криптовалюты. \n"
                         "/graph [cryptocurrency] - получить график криптовалюты.\n"
                         "/info [cryptocurrency] - получить основную информацию по крипте")


# Command handler for /graph
@dp.message_handler(commands=['graph'])
async def cmd_graph(message: types.Message):
    try:
        # Get the user's input for the cryptocurrency name
        command_args = message.get_args().split()
        if len(command_args) != 1:
            await message.answer("Неверный формат команды. Пожалуйста, используйте /graph [криптовалюта].")
            return

        cryptocurrency = command_args[0].upper()

        # Clear the current figure
        plt.clf()

        # Get cryptocurrency historical data from Binance API
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://api.binance.com/api/v3/klines?symbol={cryptocurrency}USDT&interval=1d&limit=30') as response:
                if response.status == 200:
                    data = await response.json()

                    # Extract the timestamps and closing prices from the data
                    timestamps = [entry[0] / 1000 for entry in data]
                    prices = [float(entry[4]) for entry in data]

                    # Plot the graph
                    plt.plot(timestamps, prices)
                    plt.xlabel('Date')
                    plt.ylabel(f'{cryptocurrency} Цена (USDT)')
                    plt.title(f'{cryptocurrency} График цен')
                    plt.xticks(rotation=45)
                    plt.grid(True)

                    # Save the graph as an image file
                    graph_filename = f'{cryptocurrency}_graph.png'
                    plt.savefig(graph_filename)

                    # Send the graph image to the user
                    with open(graph_filename, 'rb') as graph_file:
                        await message.answer_photo(graph_file)

                    # Remove the graph image file
                    os.remove(graph_filename)
                else:
                    await message.answer("Не удалось получить данные о криптовалюте. Возможно неправильное название крипты. Пожалуйста, повторите попытку позже.")
    except Exception as e:
        await message.answer("")


# Command handler for /info
@dp.message_handler(commands=['info'])
async def cmd_info(message: types.Message):
    try:
        # Get the user's input for the cryptocurrency name
        command_args = message.get_args().split()
        if len(command_args) != 1:
            await message.answer("Неверный формат команды. Пожалуйста, используйте /info [cryptocurrency].")
            return

        cryptocurrency = command_args[0]

        # Get cryptocurrency information from CoinGecko API
        url = f'{coin_gecko_base_url}/coins/{cryptocurrency.lower()}'
        response = await aiohttp.ClientSession().get(url)

        if response.status == 200:
            data = await response.json()

            # Extract relevant information from the response
            name = data['name']
            symbol = data['symbol']
            current_price = data['market_data']['current_price']['usd']
            market_cap = data['market_data']['market_cap']['usd']
            volume = data['market_data']['total_volume']['usd']

            info_message = f"Name: {name}\n" \
                           f"Symbol: {symbol}\n" \
                           f"Current Price: {current_price} USD\n" \
                           f"Market Cap: {market_cap} USD\n" \
                           f"24h Volume: {volume} USD"

            await message.answer(info_message)
        else:
            await message.answer("Не удалось получить информацию о криптовалюте. Пожалуйста, повторите попытку позже.")
    except Exception as e:
        await message.answer("При получении информации о криптовалюте произошла ошибка. Пожалуйста, повторите попытку позже.")

# Command handler for /usdt
@dp.message_handler(commands=['usdt'])
async def cmd_btc(message: types.Message):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.binance.com/api/v3/ticker/price') as response:
                if response.status == 200:
                    rates = await response.json()
                    usdt_price = next((symbol['price'] for symbol in rates if symbol['symbol'] == 'BUSDUSDT'), None)

                    if usdt_price:
                        exchange_rate_response = requests.get(exchange_rate_api)
                        exchange_rate_data = exchange_rate_response.json()
                        usd_to_rub_rate = exchange_rate_data['rates']['RUB']
                        usd_to_kzt_rate = exchange_rate_data['rates']['KZT']
                        usdt_price_rub = float(usdt_price) * usd_to_rub_rate
                        usdt_price_kzt = float(usdt_price) * usd_to_kzt_rate
                        await message.answer(f"Цена BUSDT (USDT): {usdt_price} USD | {usdt_price_rub} RUB | {usdt_price_kzt} KZT")
                    else:
                        await message.answer("Не удалось получить цену BUSDT (USDT). Пожалуйста, повторите попытку позже.")
                else:
                    await message.answer("Не удалось получить курсы криптовалют. Пожалуйста, повторите попытку позже.")
    except Exception as e:
        await message.answer("Произошла ошибка при поиске курсов криптовалют. Пожалуйста, повторите попытку позже.")


# Command handler for /btc and /eth
@dp.message_handler(commands=['btc', 'eth'])
async def cmd_crypto(message: types.Message):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.binance.com/api/v3/ticker/price') as response:
                if response.status == 200:
                    rates = await response.json()
                    cryptocurrency = message.text[1:].upper()
                    symbol = f'{cryptocurrency}USDT'
                    crypto_price = get_crypto_price(rates, symbol)

                    if crypto_price:
                        exchange_rate_response = await session.get(exchange_rate_api)
                        if exchange_rate_response.status == 200:
                            exchange_rate_data = await exchange_rate_response.json()
                            usd_to_rub_rate = exchange_rate_data['rates']['RUB']
                            usd_to_kzt_rate = exchange_rate_data['rates']['KZT']
                            crypto_price_rub = float(crypto_price) * usd_to_rub_rate
                            crypto_price_kzt = float(crypto_price) * usd_to_kzt_rate
                            await message.answer(f"{cryptocurrency} цена: {crypto_price} USD | {crypto_price_rub} RUB | {crypto_price_kzt} KZT")
                    else:
                        await message.answer(f"Не удалось получить {cryptocurrency} цену. Пожалуйста, повторите попытку позже.")
                else:
                    await message.answer("Не удалось получить курсы криптовалют. Пожалуйста, повторите попытку позже.")
    except Exception as e:
        await message.answer("Произошла ошибка при поиске курсов криптовалют. Пожалуйста, повторите попытку позже.")

@dp.message_handler(commands=['rate'])
async def cmd_rates(message: types.Message):
    try:
        # Get the user's input for the cryptocurrency name
        command_args = message.get_args().split()
        if len(command_args) != 1:
            await message.answer("Неверный формат команды. Пожалуйста, используйте /rate [криптовалюта].")
            return

        cryptocurrency = command_args[0].upper()

        # Get cryptocurrency rates from Binance API
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.binance.com/api/v3/ticker/price') as response:
                if response.status == 200:
                    rates = await response.json()
                    symbol = f'{cryptocurrency}USDT'
                    crypto_price = get_crypto_price(rates, symbol)

                    if crypto_price:
                        # Get USD to RUB and KZT exchange rates
                        exchange_rate_response = requests.get(exchange_rate_api)
                        if exchange_rate_response.status_code == 200:
                            exchange_rate_data = exchange_rate_response.json()
                            usd_to_rub_rate = exchange_rate_data['rates']['RUB']
                            usd_to_kzt_rate = exchange_rate_data['rates']['KZT']

                            crypto_price_rub = float(crypto_price) * usd_to_rub_rate
                            crypto_price_kzt = float(crypto_price) * usd_to_kzt_rate
                            await message.answer(f"{cryptocurrency} цена: {crypto_price} USD | {crypto_price_rub} RUB | {crypto_price_kzt} KZT")
                        else:
                            await message.answer("Не удалось получить обменный курс доллара США к рублю.")
                    else:
                        await message.answer(f"Не удалось получить {cryptocurrency} цена. Убедитесь, что название криптовалюты указано правильно.")
                else:
                    await message.answer("Не удалось получить курсы криптовалют. Пожалуйста, повторите попытку позже.")
    except Exception as e:
        await message.answer("Произошла ошибка при поиске курсов криптовалют. Пожалуйста, повторите попытку позже.")


# Command handler for /rates
@dp.message_handler(commands=['rates'])
async def cmd_rates(message: types.Message):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.binance.com/api/v3/ticker/price') as response:
                if response.status == 200:
                    rates = await response.json()

                    # crypto
                    btc_price = get_crypto_price(rates, 'BTCUSDT')
                    eth_price = get_crypto_price(rates, 'ETHUSDT')
                    usdt_price = get_crypto_price(rates, 'BUSDUSDT')
                    bnb_price = get_crypto_price(rates, 'BNBUSDT')
                    usdcoin_price = get_crypto_price(rates, 'USDCUSDT')
                    xrp_price = get_crypto_price(rates, 'XRPUSDT')
                    ada_price = get_crypto_price(rates, 'ADAUSDT')
                    doge_price = get_crypto_price(rates, 'DOGEUSDT')
                    trx_price = get_crypto_price(rates, 'TRXUSDT')
                    sol_price= get_crypto_price(rates, 'SOLUSDT')
                    ltc_price = get_crypto_price(rates, 'LTCUSDT')
                    dot_price = get_crypto_price(rates, 'DOTUSDT')
                    matic_price= get_crypto_price(rates, 'MATICUSDT')

                    if btc_price and eth_price and usdt_price and bnb_price:
                        exchange_rate_response = await session.get(exchange_rate_api)
                        if exchange_rate_response.status == 200:
                            exchange_rate_data = await exchange_rate_response.json()
                            usd_to_rub_rate = exchange_rate_data['rates']['RUB']
                            usd_to_kzt_rate = exchange_rate_data['rates']['KZT']

                            #rub crypto
                            btc_price_rub = float(btc_price) * usd_to_rub_rate
                            eth_price_rub = float(eth_price) * usd_to_rub_rate
                            usdt_price_rub = float(usdt_price) * usd_to_rub_rate
                            bnb_price_rub = float(bnb_price) * usd_to_rub_rate
                            usdcoin_price_rub = float(usdcoin_price) * usd_to_rub_rate
                            xrp_price_rub = float(xrp_price) * usd_to_rub_rate
                            ada_price_rub = float(ada_price) * usd_to_rub_rate
                            doge_price_rub = float(doge_price) * usd_to_rub_rate
                            trx_price_rub = float(trx_price) * usd_to_rub_rate
                            sol_price_rub = float(sol_price) * usd_to_rub_rate
                            ltc_price_rub = float(ltc_price) * usd_to_rub_rate
                            dot_price_rub = float(dot_price) * usd_to_rub_rate
                            matic_price_rub = float(matic_price) * usd_to_rub_rate


                            #kzt crypto
                            btc_price_kzt = float(btc_price) * usd_to_kzt_rate
                            eth_price_kzt = float(eth_price) * usd_to_kzt_rate
                            usdt_price_kzt= float(usdt_price) * usd_to_kzt_rate
                            bnb_price_kzt = float(bnb_price) * usd_to_kzt_rate
                            usdcoin_price_kzt = float(usdcoin_price) * usd_to_kzt_rate
                            xrp_price_kzt = float(xrp_price) * usd_to_kzt_rate
                            ada_price_kzt = float(ada_price) * usd_to_kzt_rate
                            doge_price_kzt = float(doge_price) * usd_to_kzt_rate
                            trx_price_kzt = float(trx_price) * usd_to_kzt_rate
                            sol_price_kzt = float(sol_price) * usd_to_kzt_rate
                            ltc_price_kzt = float(ltc_price) * usd_to_kzt_rate
                            dot_price_kzt = float(dot_price) * usd_to_kzt_rate
                            matic_price_kzt = float(matic_price) * usd_to_kzt_rate

                            await message.answer(f"Цена Bitcoin (BTC): {btc_price} USDT | {btc_price_rub} RUB | {btc_price_kzt} KZT")
                            await message.answer(f"Цена Ethereum (ETH): {eth_price} USDT | {eth_price_rub} RUB | {eth_price_kzt} KZT")
                            await message.answer(f"Цена BUSD/USDT (USDT): {usdt_price} USDT | {usdt_price_rub} RUB | {usdt_price_kzt} KZT")
                            await message.answer(f"Цена BNB/USDT (BNB): {bnb_price} USDT | {bnb_price_rub} RUB | {bnb_price_kzt} KZT")
                            await message.answer(f"Цена USDC/USDT (USD Coin): {usdcoin_price} USDT | {usdcoin_price_rub} RUB | {usdcoin_price_kzt} KZT")
                            await message.answer(f"Цена XRP/USDT (Ripple): {xrp_price} USDT | {xrp_price_rub} RUB | {xrp_price_kzt} KZT")
                            await message.answer(f"Цена ADA/USDT (Cardano): {ada_price} USDT | {ada_price_rub} RUB | {ada_price_kzt} KZT")
                            await message.answer(f"Цена DOGE/USDT (Dogecoin): {doge_price} USDT | {doge_price_rub} RUB | {doge_price_kzt} KZT")
                            await message.answer(f"Цена TRX/USDT (TRON): {trx_price} USDT | {trx_price_rub} RUB | {trx_price_kzt} KZT")
                            await message.answer(f"Цена SOL/USDT (Solana): {sol_price} USDT | {sol_price_rub} RUB | {sol_price_kzt} KZT")
                            await message.answer(f"Цена LTC/USDT (Litecoin): {ltc_price} USDT | {ltc_price_rub} RUB | {ltc_price_kzt} KZT")
                            await message.answer(f"Цена DOT/USDT (Polkadot): {dot_price} USDT | {dot_price_rub} RUB | {dot_price_kzt} KZT")
                            await message.answer(f"Цена MATIC/USDT (Polygon): {matic_price} USDT | {matic_price_rub} RUB | {matic_price_kzt} KZT")
                        else:
                            await message.answer("Не удалось получить обменный курс доллара США к рублю.")
                    else:
                        await message.answer("Не удалось получить курсы криптовалют. Пожалуйста, повторите попытку позже.")
                else:
                    await message.answer("Не удалось получить курсы криптовалют. Пожалуйста, повторите попытку позже.")
    except Exception as e:
        await message.answer("Произошла ошибка при поиске курсов криптовалют. Пожалуйста, повторите попытку позже.")


# Command handler for /threshold
@dp.message_handler(commands=['threshold'])
async def cmd_threshold(message: types.Message):
    try:
        # Parse the cryptocurrency and threshold value from the message
        command_args = message.get_args().split()
        if len(command_args) != 2:
            await message.answer("Неверный формат команды. Пожалуйста, используйте /threshold [cryptocurrency] [threshold_value].")
            return

        cryptocurrency = command_args[0].upper()
        threshold = float(command_args[1])

        # Store the threshold for the user
        user_id = message.from_user.id
        thresholds = user_thresholds.setdefault(user_id, {})
        thresholds[cryptocurrency] = {
            'threshold': threshold,
            'triggered': False
        }

        await message.answer(f"{cryptocurrency} порог установлен на: {threshold} USDT")
    except (ValueError, TypeError):
        await message.answer("Неверное пороговое значение. Пожалуйста, укажите действительное число.")


# Get the price of a cryptocurrency from the rates data
def get_crypto_price(rates, symbol):
    for symbol_data in rates:
        if symbol_data['symbol'] == symbol:
            return symbol_data['price']
    return None


# Check if the cryptocurrency price exceeds the user's threshold
async def check_thresholds():
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://api.binance.com/api/v3/ticker/price') as response:
                    if response.status == 200:
                        rates = await response.json()

                        for user_id, thresholds in user_thresholds.items():
                            for cryptocurrency, threshold_data in thresholds.items():
                                threshold = threshold_data['threshold']
                                triggered = threshold_data['triggered']
                                symbol = f'{cryptocurrency}USDT'

                                crypto_price = get_crypto_price(rates, symbol)
                                if crypto_price:
                                    crypto_price = float(crypto_price)

                                    if crypto_price > threshold and not triggered:
                                        await bot.send_message(
                                            user_id, f"{cryptocurrency} цена превысила {threshold} USD!"
                                        )
                                        thresholds[cryptocurrency]['triggered'] = True
                                    elif crypto_price <= threshold and triggered:
                                        thresholds[cryptocurrency]['triggered'] = False

            await asyncio.sleep(10)  # Check every 10 seconds
        except Exception as e:
            logging.error(f"Произошла ошибка при проверке криптовалютных порогов: {str(e)}")


# Start the bot
if __name__ == '__main__':
    from aiogram import executor

    asyncio.ensure_future(check_thresholds())

    executor.start_polling(dp, skip_updates=True)
