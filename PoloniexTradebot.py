#! python3
# coding=utf-8


import json
import os
import sys
from datetime import datetime

import ccxt

import tradebot_config

while True:  # First check for user BTC Value input
    try:
        budget = float(sys.argv[1])  # .format('0.001')
        break
    except ValueError:  # Print an Exception (error) if there is no input
        print("Input Budget: python AllCoinsInBTC.py 0.0001")
        budget = 0.0000

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


# set time labels
MINUTE, HOUR, DAY = 60, 60 * 60, 60 * 60 * 24
WEEK = DAY * 7
YEAR = DAY * 365
MONTH = YEAR / 12


def logo():
    print(" ------------------------------------------------------")
    print(' | _______                __         __           __   |')
    print(' ||_     _|.----.---.-.--|  |.-----.|  |--.-----.|  |_ |')
    print(' |  |   |  |   _|  _  |  _  ||  -__||  _  |  _  ||   _||')
    print(' |  |___|  |__| |___._|_____||_____||_____|_____||____||')


def decor(func):
    def wrap():
        print(" ---------------------------------------------------------------")
        func()
        print(" ---------------------------------------------------------------")
    return wrap


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
        0: exit_tradebot
    }
    print(' ')
    menuitem = int(input('                 Please input options choice: '))
    if 0 < menuitem < 10:
        if menuitem is (5 or 8 or 7):
            options_choices[menuitem](True)
        else:
            options_choices[menuitem]()

    else:
        print(' ')
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
    get_update()
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
            print('             json/poloniex_markets.json               saved')

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
        finally:
            print("                     Poloniex data saved")

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
    print('             json/poloniex_balances.json              saved')
    return()


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
        return(wallet)


def collect_orders(show=False):
    global item
    market = 'MARKET'
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
    btc_balance = total_balance()
    print("         Amount of _BTC markets   : ", max_index + 1)
    print("                    BTC available : ", btc_balance)
    advice = btc_balance / (max_index + 1)
    print("                    budget advice : ", advice)
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
                    # print("AltWorth is higher then budget")
                    OrderWorth = float(AltWorth) - float(budget)  # Calculate how much to sell in BTC
                    orderPrint = "                   AltSellWorth = ₿ %.8f" % OrderWorth
                    AltAmount = float(OrderWorth) / float(Bid)  # Calculate how much AltCoins to Sell
                    List = Bids
                    break  # stop if loop
                else:  # ------------------------------#Lower  = BUY
                    # print("AltWorth is lower then budget")
                    side = "BUY"
                    OrderWorth = float(budget) - float(AltWorth)  # Calculate how much to buy in BTC
                    orderPrint = "                    AltBuyWorth = ₿ %.8f" % OrderWorth
                    AltAmount = float(OrderWorth) / float(Ask)  # Calculate how much AltCoins to Buy
                    List = Asks
                    break  # stop else loop
            except:
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
                    print("              ---! ", AltCoin, "Order To Small To Place !---")
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
                        price = float(List[i][0])
                        amount = float(List[i][1])
                        available = (price * amount)
                        order = order + available
                        if show:
                            print("  |   (", i + 1, ") %.8f" % available, AltCoin, "    for    ₿ %.8f" % price, "   |")
                        i = i + 1
                    total = AltAmount * price
                    if show:
                        print("   ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾ ")
                        print("        Order will use ", i, " available orders")
                        print("")
                        print("             amount:   %.8f" % AltAmount, AltCoin)
                        print("              price: ₿ %.8f" % price)
                        print("              total: ₿ %.8f" % total)
                    now = get_time()
                    try:
                        if side == "BUY":
                            print("                 ---| Adding BUY to order list |---")
                            item = {"symbol": symbol,
                                    "type": market,
                                    "side": side,
                                    "AltAmount": AltAmount,
                                    "price": price,
                                    "total": total,
                                    "alt": AltCoin,
                                    "time": now
                                    }
                            # polo.create_order(symbol, market, side, AltAmount, price)
                            break
                        else:
                            print("                 ---| Adding SELL to order list |---")
                            item = {"symbol": symbol,
                                    "type": market,
                                    "side": side,
                                    "AltAmount": AltAmount,
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
    with open('json/orderlist.json', 'r') as openOrderlist:  # Opening JSON file
        orders = json.load(openOrderlist)  # Reading from json file
    nr = 0
    max_index = len(orders) - 1
    now = get_time()
    print("                    orders: ", max_index + 1)
    print("{:>9}".format("| Order"), "{:<22}".format("|       Amount "), "{:>12}".format("|    Price   "),
          "{:>15}".format("|   Total     |"), " status")
    while nr <= max_index:  # while = loop through PoloniexCoins List until max_index
        symbol = orders[nr]['symbol']
        type = orders[nr]['type']
        side = orders[nr]['side']
        amount = orders[nr]['AltAmount']
        price = orders[nr]['price']
        total = orders[nr]['total']
        alt = orders[nr]['alt']
        if place:
            try:
                polo.create_order(symbol, type, side, total)
                status = "Complete"
            except:
                status = "INCOMPLETE"
        else:
            status = "---"

        print(f"{side:>8}",
              "{:>16}".format(" %.8f" % amount),
              f"{alt:<7}",
              " %.8f" % price,
              "  %.8f" % total,
              status)
        nr = nr + 1
    menu()


def get_time():
    now = datetime.now()
    dt_string = now.strftime("%Y/%m/%d %H:%M:%S")
    return dt_string


if __name__ == "__main__":

    logo()
    menu()

