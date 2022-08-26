#! python3
# coding=utf-8
import time

import json
import os
import sys
import ccxt
import tradebot_config
from datetime import datetime

while True:  # First check for user BTC Value input
    try:
        budget = float(sys.argv[1])  # .format('0.0005')
        break
    except ValueError:  # Print an Exception (error) if there is no input
        print("Input Budget: python PoloniexTradebot.py 0.0001")
        budget = 0.0005

while True:  # Setup to connect to Poloniex API
    try:
        polo = ccxt.poloniex({
            'apiKey': tradebot_config.SECRET_API_KEY,
            'secret': tradebot_config.SECRET_API_SECRET,
            'options': {'createMarketBuyOrderRequiresPrice': False}
        })
        print(" ")
        print('            |‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾| ')
        print("            |   Connected to Poloniex.com   | ")
        fetch_info = polo.fetch_balance()['info'][0]['accountId']
        print('            |  AccountId', fetch_info, ' | ')
        print('            |   pip install --upgrade ccxt  | ')
        print('            | poloniex.com/signup?c=F8GSBSS5| ')
        print('            |                               | ')
        print('             ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾ ')
        break
    except ConnectionError:
        print("Can not connect to Poloniex API")
        exit(1)


def decor(func):
    def wrap():
        print(" ---------------------------------------------------------------")
        func()
        print(" ---------------------------------------------------------------")
    return wrap


@decor
def logo():

    print(C.F.gr,
          "      _____      _             _                   ")
    print("      |  __ \    | |           (_)                  ")
    print("      | |__) |__ | | ___  _ __  _  _____  __        ")
    print("      |  ___/ _ \| |/ _ \| '_ \| |/ _ \ \/ /        ")
    print("      | |  | (_) | | (_) | | | | |  __/>  <         ")
    print("      |_|  _\___/|_|\___/|_| |_|_|\___/_/\_\     _      ")
    print("          |__   __|          | |    | |         | |     ")
    print("             | |_ __ __ _  __| | ___| |__   ___ | |_    ")
    print("             | | '__/ _` |/ _` |/ _ \ '_ \ / _ \| __|   ")
    print("             | | | | (_| | (_| |  __/ |_) | (_) | |_    ")
    print("             |_|_|  \__,_|\__,_|\___|_.__/ \___/ \__|   ", C.rst)


@decor
def menu_list():
    print('            |‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾|')
    print('            |  1: start_bot                 |')
    print('            |  2: collect_orders            |')
    print('            |  3: order_list                |')
    print('            |  4: options                   |')
    print('            |  0: exit_tradebot             |')
    print('             ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾ ')


def menu():
    menu_list()
    menuchoices = {
        1: start_bot,
        2: collect_orders,
        3: order_list,
        4: options,
        0: exit_tradebot
    }
    print(' ')
    try:
        menuitem = int(input('                 Please input menu choice: '))
        if menuitem < 9:
            menuchoices[menuitem]()
        else:
            print(' ')
            print("          Something went wrong! Call the police!")
            print(' ')
            menu()
    except (KeyError, ValueError):
        print("          Something went wrong! Enter an option number!")
        menu()


@decor
def options_list():
    print('            |‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾|')
    print('            |  All functions                |')
    print('            |  1: getUpdate                 |')
    print('            |  2: market_list               |')
    print('            |  3: listed                    |')
    print('            |  4: makePoloniexCoins         |')
    print('            |  5: total_balance             |')
    print('            |  6: get_open_orders           |')
    print('            |  7: collect_orders            |')
    print('            |  8: order_list                |')
    print('            |  9: Color test                |')
    print('             ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾ ')


def options():
    options_list()
    options_choices = {
        1: get_update,
        2: market_list,
        3: listed,
        4: make_poloniex_coins,
        5: total_balance,
        6: get_open_orders,
        7: collect_orders,
        8: order_list,
        9: print_format_table,
        0: exit_tradebot
    }
    print(' ')
    menuitem = int(input('                 Please choose option: '))
    if 0 < menuitem < 10:
        if menuitem is (5 or 8 or 7):
            options_choices[menuitem](True)
        else:
            options_choices[menuitem]()
    else:
        print(' ')
        print("          Something went wrong! Call the police!")
        print(' ')
        menu()


def exit_tradebot():
    print("    ______  __ __   ____  ____   __  _      __ __   ___   __ __  ")
    print("   |      ||  |  | /    ||    \ |  |/ ]    |  |  | /   \ |  |  | ")
    print("   |      ||  |  ||  o  ||  _  ||  ' /     |  |  ||     ||  |  | ")
    print("   |_|  |_||  _  ||     ||  |  ||    \     |  ~  ||  O  ||  |  | ")
    print("     |  |  |  |  ||  _  ||  |  ||     \    |___, ||     ||  :  | ")
    print("     |  |  |  |  ||  |  ||  |  ||  .  |    |     ||     ||     | ")
    print("     |__|  |__|__||__|__||__|__||__|\_|    |____/  \___/  \__,_| ")
    exit(1)


def start_bot():
    market_list()
    listed()
    make_poloniex_coins()
    collect_orders()
    order_list(True)


def get_update():  # 1
    pathjson = './json'
    jsonExist = os.path.exists(pathjson)
    pathbook = './orderbooks'
    bookExist = os.path.exists(pathbook)

    if not jsonExist:
        os.makedirs(pathjson, exist_ok=False)
        print("               Created the Json directory!")
    if not bookExist:
        os.makedirs(pathbook, exist_ok=False)
        print("               Created the Orderbook directory!")
    while True:
        try:
            fetch_markets = polo.fetch_markets()
            with open("json/poloniex_markets.json", "w") as outfile:
                json.dump(fetch_markets, outfile, sort_keys=True, separators=(',', ':'))
            print(C.disable, '            json/poloniex_markets.json               saved')

            polo_currencies = polo.fetch_currencies()
            with open("json/poloniex_currencies.json", "w") as outfile:
                json.dump(polo_currencies, outfile, sort_keys=True, separators=(',', ':'))
            print('             json/poloniex_currencies.json            saved')

            polo_fetch = polo.fetch_balance()
            with open("json/poloniex_balances_full.json", "w") as outfile:
                json.dump(polo_fetch, outfile, sort_keys=True, separators=(',', ':'))
            print('             json/poloniex_balances_full.json         saved')

            polo_tickers = polo.fetch_tickers()
            with open("json/poloniex_tickers.json", "w") as outfile:
                json.dump(polo_tickers, outfile, sort_keys=True, separators=(',', ':'))
            print('             json/poloniex_tickers.json               saved')

            with open('json/poloniex_balances_full.json', 'r') as openfile:  # Opening JSON file
                balance_full = json.load(openfile)['info'][0]['balances']  # Reading from json file
            break
        except TimeoutError:
            print("             An TimeoutError occurred, please retry")
            exit(1)

    myBalances = []
    counter = 0
    max_index = len(balance_full) - 1
    while counter <= max_index:
        currency = balance_full[counter]['currency']
        available = balance_full[counter]['available']
        myBalances.append(currency + ' ' + available)
        counter = counter + 1

    res = dict()  # create new dictionary to fill
    for sub in myBalances:
        key, *val = sub.split()  # split() for key
        res[key] = val  # packing value list
    with open("json/poloniex_balances.json", "w") as outfile:
        json.dump(res, outfile, sort_keys=True, separators=(',', ':'))
    print('             json/poloniex_balances.json              saved', C.rst)
    return ()


def market_list():  # 2
    with open('json/poloniex_markets.json', 'r') as openfile:  # Opening JSON file
        json_object = json.load(openfile)  # Reading from json file
    counter = 0
    live_market = []
    max_index = len(json_object) - 1
    while counter <= max_index:
        id = json_object[counter]['id']
        active = json_object[counter]['active']
        if active is True:
            live_market.append(id)
        counter = counter + 1
    with open("json/poloniex_live_market.txt", 'w') as outfile:  # open file in write mode
        for market in live_market:
            outfile.write("%s\n" % market)  # write each item on a new line
    print('   All live markets as json/poloniex_live_market.txt  saved')
    Btc_Markets = []
    for x in sorted(live_market):
        if "_BTC" in x:
            Btc_Markets.append(x)
    with open("json/poloniex_Btc_Markets.txt", 'w') as outfile:  # open file in write mode
        for pair in Btc_Markets:
            outfile.write("%s\n" % pair)  # write each item on a new line
    print('   All _BTC markets as json/poloniex_Btc_Markets.txt  saved')
    listed()


def listed():  # 3
    with open('json/poloniex_currencies.json', 'r') as openfile:  # Opening JSON file
        json_object = json.load(openfile)  # Reading from json file
    keyList = json_object.keys()
    ListedCoins = []
    for x in sorted(keyList):
        delisted = json_object[x]['info']['delisted']
        if delisted is False:
            ListedCoins.append(x)
    with open("json/poloniex_ListedCoins.txt", 'w') as outfile:  # open file in write mode
        for coins in ListedCoins:
            outfile.write("%s\n" % coins)  # write each item on a new line
    print('   All listed coins as json/poloniex_ListedCoins.txt  saved')
    make_poloniex_coins()


def make_poloniex_coins():  # 4
    BtcMarkets = []  # empty list to read list from a file
    with open("json/poloniex_Btc_Markets.txt", 'r') as outfile:
        for line in outfile:
            x = line[:-1]  # remove linebreak from a current name
            BtcMarkets.append(x)  # add current item to the list

    Listed = []  # empty list to read list from a file
    with open("json/poloniex_ListedCoins.txt", 'r') as outfile2:
        for line2 in outfile2:
            y = line2[:-1]  # remove linebreak from a current name
            Listed.append(y)  # add current item to the list

    PoloniexCoinlist = []
    counter = 0
    max_index = len(Listed) - 1
    while counter <= max_index:
        coin = Listed[counter]
        symbol = coin + "_BTC"
        for x in BtcMarkets:
            if symbol == x:
                PoloniexCoinlist.append(coin)
        counter = counter + 1

    with open("json/poloniex_btc_pairs.txt", 'w') as outfile:  # open file in write mode
        for coin in PoloniexCoinlist:
            outfile.write("%s\n" % coin)  # write each item on a new line
        print('        BTC markets as json/  poloniex_btc_pairs.txt  saved')
    total_balance()


def get_open_orders():  # 6
    """
    while True:  # First check if the coinpair already has an Open Order & Cancel it
        try:
            fetchOpenOrders = polo.fetch_open_orders()  # Collect the open orders of the coinpair
            print(fetchOpenOrders)
            polo.cancel_order( id, symbol)

            if fetchOpenOrders:  # if the openorders are not empty Cancel the Order
                returnOrderNumber = fetchOpenOrders()[pair][0]['orderNumber']  # Collect last orderNumber
                returnOrderAmount = fetchOpenOrders()[pair][0]['amount']  # Collect OrderAmount
                print("     Open Order: ", returnOrderNumber, "Total Amount in BTC: ",
                      returnOrderAmount)  # OpenOrder Info
                cancelOrder = polo.cancelOrder(returnOrderNumber)  # cancel order with latest orderNumber
                print("---!CANCEL Complete!---")  # Reloop the OpenOrder Check
                break
            else:  # if the openorders are not empty
                break
        except:  # Print an Exception (error) if script can't collect Orders
            break
    """
    print('             getOpenOrders #6')
    menu()


def total_balance(show=False):
    Coins = []
    with open("json/poloniex_btc_pairs.txt", 'r') as openBtcpair:  # Get list from a local file
        for line in openBtcpair:  # remove linebreak from a current name
            x = line[:-1]
            Coins.append(x)
    with open('json/poloniex_balances.json', 'r') as openBalances:  # Reading from json file
        balances = json.load(openBalances)
    with open('json/poloniex_tickers.json', 'r') as openTickers:
        tickers = json.load(openTickers)
    wallet = 0.0
    btcfree = float(balances.get("BTC")[0])
    wallet = wallet + btcfree
    if show:
        print("{:>8}".format("BTC"), "{:>16}".format(" %.8f" % btcfree))
    counter = 0
    max = len(Coins) - 1
    while counter <= max:
        x = Coins[counter]
        if x in balances:
            pair = str(x + "/BTC")
            LastPrice = float((tickers[pair]['last']))
            amount = balances.get(x)[0]
            altTotal = float(LastPrice) * float(amount)
            if show:
                print(f"{x:>8}", "{:>16}".format(" %.8f" % altTotal))
            wallet = wallet + altTotal
        else:
            altTotal = float(0.0)
            wallet = wallet + altTotal
        counter = counter + 1
    if show:
        print("         total btc available: ", wallet)
        options()
    else:
        return (wallet)


def advice(show=False):
    PoloniexCoins = []
    with open("json/poloniex_btc_pairs.txt", 'r') as openBtcpair:  # Get list from a local file
        for line in openBtcpair:  # remove linebreak from a current name
            x = line[:-1]
            PoloniexCoins.append(x)
    max_index = len(PoloniexCoins) - 1
    btc_balance = total_balance()
    input_advice = round((btc_balance * 0.8) / (max_index + 1), 5)
    btc_balance = total_balance()
    print("             Poloniex has   : ", max_index + 1, "Bitcoin markets")
    print("              BTC available :  ₿ %.8f" % btc_balance)
    if show:
        print("              budget  input :  ₿ %.5f" % budget)
        if budget < input_advice:
            print("          max budget advice :", C.F.gr, "₿ %.5f" % input_advice, C.rst)
        else:
            print("          max budget advice :", C.F.rd, "₿ %.5f" % input_advice, C.rst)
    else:
        return input_advice


def collect_orders(show=False):
    global item, orderPrint
    market = 'LIMIT' # LIMIT_MAKER - MARKET
    PoloniexCoins = []
    with open("json/poloniex_btc_pairs.txt", 'r') as openBtcpair:  # Get list from a local file
        for line in openBtcpair:  # remove linebreak from a current name
            x = line[:-1]
            PoloniexCoins.append(x)
    with open('json/poloniex_balances.json', 'r') as openBalances:  # Reading from json file
        balances = json.load(openBalances)
    with open('json/poloniex_tickers.json', 'r') as openTickers:
        tickers = json.load(openTickers)

    counter = 0
    max_index = len(PoloniexCoins) - 1
    orderlist = []
    while counter <= max_index:  # while = loop through PoloniexCoins List until max_index
        AltCoin = PoloniexCoins[counter]  # Every loop change variable AltCoin to counter (0=AMP, 1=ARDR, 2=BAT...)
        symbol = str(AltCoin + "/BTC")
        pair = str(AltCoin + "_BTC")
        if AltCoin in balances:
            jv1 = balances.get(AltCoin)[0]
            AltTotal = float(jv1)  # Get your amount of the altcoin
        else:
            AltTotal = float(0.0)
        LastPrice = float((tickers[symbol]['last']))
        AltWorth = float(LastPrice) * float(AltTotal)
        headline = str("  ₿ %.8f" % LastPrice)
        fetchorderbook = polo.fetch_order_book(pair, 5)
        with open("orderbooks/" + pair + ".json", "w") as outfile:
            json.dump(fetchorderbook, outfile)
        with open("orderbooks/" + pair + ".json", 'r') as openfile:
            orderbook = json.load(openfile)  # Reading from json file
        Asks = orderbook['asks']  # [[Price, Amount],[...]]
        Ask = Asks[0][0]  # Collect latest Sell(ask) prices
        Bids = orderbook['bids']  # [[Amount, Price],[...]]
        Bid = Bids[0][0]  # Collect latest Buy (bid) prices
        while True:  # Check if the AltWorth is Higher or Lower than Budget (script-input)
            try:
                if float(AltWorth) >= float(budget):  # Higher = SELL
                    side = "SELL"
                    OrderWorth = float(AltWorth) - float(budget)  # Calculate how much to sell in BTC
                    AltAmount = float(OrderWorth) / float(Bid)  # Calculate how much AltCoins to Sell
                    List = Bids
                    break  # stop if loop
                else:  # ------------------------------#Lower  = BUY
                    side = "BUY"
                    OrderWorth = float(budget) - float(AltWorth)  # Calculate how much to buy in BTC
                    AltAmount = float(OrderWorth) / float(Ask)  # Calculate how much AltCoins to Buy
                    List = Asks
                    break  # stop else loop
            except Exception:
                OrderWorth = 0.000001
                AltAmount = 0.0
                side = "ERROR"
                List = []
                orderPrint = "  The Orderbook does not work, Maybe no orders."
                break
        while True:
            try:
                MinOrder = 0.0001  # Minimal order worth in BTC = Poloniex Trading Rule
                if MinOrder > OrderWorth:  # Compare MinOrder with AltSellWorth
                    print(C.disable, "          ---! ", AltCoin, "Order To Small To Place !---", C.rst)
                    break  # stop if loop
                else:  # Show
                    i = 0
                    if show:
                        print("")
                        print("  |‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾", "{:<11}".format(pair), "OrderBook ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾| ")
                        print("  | Amount", "{:<7}".format(AltCoin), "      ₿ Buy  - Sell ₿               ",
                              "{:<7}".format(AltCoin), "|")
                    while i <= 4:
                        try:
                            askPrice = float(Asks[i][0])
                            askAmount = float(Asks[i][1])
                            askAvailable = (askPrice * askAmount)
                        except IndexError:
                            askAvailable = 0
                            askPrice = 0
                        try:
                            bidPrice = float(Bids[i][0])
                            bidAmount = float(Bids[i][1])
                            bidAvailable = (bidPrice * bidAmount)
                        except IndexError:
                            bidAvailable = 0
                            bidPrice = 0
                        if show:
                            print("  | %.8f" % askAvailable, "==> ₿ %.8f" % askPrice, "- ₿ %.8f" % bidPrice,
                                  " <== %.8f" % bidAvailable, " |")
                        i = i + 1

                    if show:
                        print("   ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾ ")
                        print('             orderbooks/' + pair + '.json               saved')
                        print("{:19}".format("   got %.4f" % AltTotal, "@price"), "{:11}".format(pair), headline)
                        print("               " + "{:<7}".format(AltCoin) + " are Worth: ₿ %.8f" % AltWorth)
                    if side == "BUY":
                        print(C.F.rd, "           lost", "{:<7}".format(AltCoin), " Buy = ₿ %.8f" % OrderWorth, C.rst)
                    elif side == "SELL":
                        print(C.F.gr, "         profit", "{:<7}".format(AltCoin), "Sell = ₿ %.8f" % OrderWorth, C.rst)
                    else:
                        print(orderPrint)

                    break
            except IndexError:
                print(" Orderbook smaller than 5")

        while True:  # 5 get the orderbook of the coinpair (All Sell & Buy Orders)
            try:
                if MinOrder > OrderWorth:
                    break
                else:
                    order = float(0.0)
                    i = 0
                    price = 0.0
                    if show:
                        print("   _________________", side, "OrderBook ___________________ ")
                    while order <= OrderWorth:
                        try:
                            price = float(List[i][0])
                            amount = float(List[i][1])
                            available = (price * amount)
                            order = order + available
                            if show:
                                print("  |   (", i + 1, ") %.8f" % available, AltCoin, "    for    ₿ %.8f" % price, "   |")
                            i = i + 1
                        except IndexError:
                            break
                    total = AltAmount * price
                    if show:
                        print("   ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾ ")
                        print("        Order will use ", i, " available orders")
                        print("")
                        print("             amount:   %.8f" % AltAmount, AltCoin)
                        print("              price: ₿ %.8f" % price)
                        print("              total: ₿ %.8f" % total)
                    now = get_time(True)
                    try:
                        if side == "BUY":
                            item = {"symbol": symbol,
                                    "type": market,
                                    "side": side,
                                    "AltAmount": AltAmount,
                                    "quantity": AltAmount,
                                    "price": price,
                                    "total": total,
                                    "alt": AltCoin,
                                    "time": now
                                    }
                            # polo.create_order(symbol, market, side, AltAmount, price)
                            break
                        else:
                            item = {"symbol": symbol,
                                    "type": market,
                                    "side": side,
                                    "AltAmount": AltAmount,
                                    "quantity": AltAmount,
                                    "price": price,
                                    "total": total,
                                    "alt": AltCoin,
                                    "time": now
                                    }
                            # polo.create_order(symbol, market, side, AltAmount, price)
                            break
                    except ValueError:
                        print("error")

                    finally:
                        orderlist.append(item)
                        break

            # end of try
            except ValueError:
                print("        ---! Can not finish the OrderBook !---")
                print("")
                break
        counter = counter + 1
    with open("json/orderlist.json", "w") as orderlistFile:
        json.dump(orderlist, orderlistFile, separators=(',', ':'))
    print('             json/orderlist.json                      saved')


def order_list(place=False):
    global status, trade_amount
    with open('json/orderlist.json', 'r') as openOrderlist:  # Opening JSON file
        orders = json.load(openOrderlist)  # Reading from json file
    nr = 0
    max_index = len(orders) - 1
    now = string2list(get_time(True))
    now = [int(i) for i in now]
    then = string2list(orders[len(orders) - 1]['time'])
    then = [int(i) for i in then]
    time_behind = list()
    for i in range(len(now)):
        item = now[i] - then[i]
        time_behind.append(item)
    lagg = ((time_behind[3] * 60 * 60) + (time_behind[4] * 60) + time_behind[5])
    print("            orders: ", max_index + 1, "      created", lagg, "seconds ago")
    print("{:>9}".format("| Order"), "{:<22}".format("|       Amount "), "{:>12}".format("|    Price   "),
          "{:>15}".format("|   Total     |"), " status")
    while nr <= max_index:  # while = loop through PoloniexCoins List until max_index
        symbol = orders[nr]['symbol']
        tradetype = orders[nr]['type']
        side = orders[nr]['side']
        amount = orders[nr]['AltAmount']
        quantity = orders[nr]['quantity']
        price = orders[nr]['price']
        total = orders[nr]['total']
        alt = orders[nr]['alt']
        if place:
            if lagg < 360:
                try:
                    if side == "BUY":
                        polo.create_order(symbol, tradetype, side, amount, price)
                        status = "Complete"
                        trade_amount = "{:>16}".format(" %.8f" % amount)
                    else:
                        polo.create_order(symbol, tradetype, side, amount, price)
                        status = "Complete"
                        trade_amount = "{:>16}".format(" %.8f" % quantity)

                except:
                    status = "INCOMPLETE"
                    trade_amount = "{:>16}".format(" %.8f" % amount)
        else:
            status = "---"
            trade_amount = "{:>16}".format(" %.8f" % amount)


        print(f"{side:>8}",
              trade_amount,
              f"{alt:<7}",
              " %.8f" % price,
              "  %.8f" % total,
              status)
        time.sleep(0.1)
        nr = nr + 1
    menu()


def get_time(time_list=False):
    now = datetime.now()
    if time_list:
        dt_string = now.strftime("%Y %m %d %H %M %S")
    else:
        dt_string = now.strftime("%Y/%m/%d %H:%M:%S")
    return dt_string


def string2list(string):
    li = list(string.split(" "))
    return li


class C:
    rst = '\033[0m'
    bold = '\033[01m'
    disable = '\033[02m'
    underline = '\033[04m'
    reverse = '\033[07m'
    strikethrough = '\033[09m'
    invisible = '\033[08m'

    class F:
        blk = '\033[30m'
        rd = '\033[31m'
        gr = '\033[32m'
        orng = '\033[33m'
        bl = '\033[34m'
        prpl = '\033[35m'
        cyn = '\033[36m'
        gry = '\033[37m'
        dgry = '\033[90m'
        lrd = '\033[91m'
        lgr = '\033[92m'
        yel = '\033[93m'
        lbl = '\033[94m'
        pnk = '\033[95m'
        lcyn = '\033[96m'

    class B:
        blk = '\033[40m'
        rd = '\033[41m'
        gr = '\033[42m'
        orng = '\033[43m'
        bl = '\033[44m'
        prpl = '\033[45m'
        cyn = '\033[46m'
        lgry = '\033[47m'


def print_format_table():
    print(C.B.gr, "testo", C.F.rd, "pesto", C.rst)
    print("pesta", C.F.cyn, "pasta", C.rst)
    for style in range(8):
        for fg in range(30, 38):
            s1 = ''
            for bg in range(40, 48):
                format = ';'.join([str(style), str(fg), str(bg)])
                s1 += '\x1b[%sm %s \x1b[0m' % (format, format)
            print(s1)
        print('\n')
    options()


if __name__ == "__main__":
    logo()
    get_update()
    advice(True)
    menu()
