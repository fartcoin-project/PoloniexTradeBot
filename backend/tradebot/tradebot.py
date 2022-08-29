#! python3
# coding=utf-8
from __future__ import print_function
import re
import time
import argparse
from time import sleep
import json
import os
import sys
import ccxt
import tradebot_config
from datetime import datetime

while True:  # Setup to connect to Poloniex API
    try:
        polo = ccxt.poloniex({
            'apiKey': tradebot_config.SECRET_API_KEY,
            'secret': tradebot_config.SECRET_API_SECRET,
            'options': {'createMarketBuyOrderRequiresPrice': False}
        })
        break
    except ConnectionError:
        print("Can not connect to Poloniex API")
        exit(1)

parser = argparse.ArgumentParser()
parser.add_argument("-b", "--budget", required=False, help="for ₿ 0.0001 Budget input '-b 1' ")
parser.add_argument("run", type=bool, nargs='?', default=False, help="run the bot without menu, best to input with --budget ")
parser.add_argument("-e", "--exclude", nargs='*', required=False, help="Input the coins to exclude from bot")
parser.add_argument("log", type=bool, nargs='?', default=False, help="extra log print in console")
args = parser.parse_args()
argv = sys.argv[1:]


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


class ProgressBar(object):
    DEFAULT = 'Progress: %(bar)s %(percent)3d%%'
    FULL = '%(bar)s %(current)d/%(total)d'  # (%(percent)3d%%) %(remaining)d to go

    def __init__(self, total, width=25, fmt=DEFAULT, symbol='=',
                 output=sys.stderr):
        assert len(symbol) == 1

        self.total = total
        self.width = width
        self.symbol = symbol
        self.output = output
        self.fmt = re.sub(r'(?P<name>%\(.+?\))d',
                          r'\g<name>%dd' % len(str(total)), fmt)

        self.current = 0

    def __call__(self):
        percent = self.current / float(self.total)
        size = int(self.width * percent)
        remaining = self.total - self.current
        bar = '   [' + self.symbol * size + ' ' * (self.width - size) + ']'

        args = {
            'total': self.total,
            'bar': bar,
            'current': self.current,
            'percent': percent * 100,
            'remaining': remaining
        }
        print('\r' + self.fmt % args, file=self.output, end='')

    def done(self):
        self.current = self.total
        self()
        print('', file=self.output)


def logo():
    print(C.F.gr,
          "       ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾")
    print("        ____       _             _ ")
    print("       |  _ \ ___ | | ___  _ __ (_) _____  __ ")
    print("       | |_) / _ \| |/ _ \| '_ \| |/ _ \ \/ / ")
    print("       |  __/ (_) | | (_) | | | | |  __/>  < ")
    print("       |_|   \___/|_|\___/|_| |_|_|\___/_/\_\ ")
    print("               _____              _      _           _ ")
    print("              |_   _| __ __ _  __| | ___| |__   ___ | |_ ")
    print("                | || '__/ _` |/ _` |/ _ \ '_ \ / _ \| __| ")
    print("                | || | | (_| | (_| |  __/ |_) | (_) | |_ ")
    print("                |_||_|  \__,_|\__,_|\___|_.__/ \___/ \__| ")
    print("     ")
    print("       ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾ ", C.rst)


def welcome():
    print("     don't forget to update CCXT every once and a while")
    print("                pip install --upgrade ccxt")
    print(" ")
    print('            |‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾| ')
    print("            |   Connected to Poloniex.com     | ")
    fetch_info = polo.fetch_balance()['info'][0]['accountId']
    print('            |  AccountId', fetch_info, '   | ')
    print('            |                                 | ')
    print('            |    ', C.F.gr, 'support with referral', C.rst, '    | ')
    print('            |          ', C.F.gr, 'F8GSBSS5', C.rst, '           | ')
    print('             ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾ ')


def get_inputs():
    while True:  # First check for user BTC Value input
        try:
            with open('config.json', 'r') as configfile:
                loadconfig = json.load(configfile)

            if args.budget is not None:
                budget_arg = f'{args.budget}'
                budget_in = float(budget_arg) / 10000  # 1.5 = ₿ 0.0001,5
                loadconfig[0]["mybudget"] = "%.8f" % budget_in

            else:
                print('tradebot.py --budget 2.' + C.disable + '50', C.rst)
                print('         == > ₿ 0.0002,' + C.disable + '50', C.rst)
                print("              ₿ 0.0001 ---> 1 ")
                budget_input = float(input('                     Input: ')) / 10000
                loadconfig[0]["mybudget"] = budget_input
            with open('config.json','w') as jsonfile:
                json.dump(loadconfig, jsonfile, indent=4) # you decide the indentation level
            break
        except(ValueError, IndexError):  # Print an Exception (error) if there is no input
            print("Print an Exception (error)")
            break


def completed():
    print(C.F.gr, "         ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾")
    print("            _    _ _   _____              _ ")
    print("           / \  | | | |_   _| __ __ _  __| | ___  ___ ")
    print("          / _ \ | | |   | || '__/ _` |/ _` |/ _ \/ __| ")
    print("         / ___ \| | |   | || | | (_| | (_| |  __/\__ \ ")
    print("        /_/   \_\_|_|   |_||_|  \__,_|\__,_|\___||___/ ")
    print("          ____                      _      _           _ ")
    print("         / ___|___  _ __ ___  _ __ | | ___| |_ ___  __| | ")
    print("        | |   / _ \| '_ ` _ \| '_ \| |/ _ \ __/ _ \/ _` | ")
    print("        | |__| (_) | | | | | | |_) | |  __/ ||  __/ (_| | ")
    print("         \____\___/|_| |_| |_| .__/|_|\___|\__\___|\__,_| ")
    print("                             |_| ")
    print("         ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾ ", C.rst)
    exit_tradebot()


def exit_tradebot():
    print(C.F.bl, "   ______  __ __   ____  ____   __  _      __ __   ___   __ __  ")
    print("   |      ||  |  | /    ||    \ |  |/ ]    |  |  | /   \ |  |  | ")
    print("   |      ||  |  ||  o  ||  _  ||  ' /     |  |  ||     ||  |  | ")
    print("   |_|  |_||  _  ||     ||  |  ||    \     |  ~  ||  O  ||  |  | ")
    print("     |  |  |  |  ||  _  ||  |  ||     \    |___, ||     ||  :  | ")
    print("     |  |  |  |  ||  |  ||  |  ||  .  |    |     ||     ||     | ")
    print("     |__|  |__|__||__|__||__|__||__|\_|    |____/  \___/  \__,_| ", C.rst)
    exit(1)


def get_update(show=False):  # 1
    print("")
    if not os.path.exists('./json'):
        os.makedirs('./json', exist_ok=False)
        if args.log: print("               Created the Json directory!")
    if not os.path.exists('./orderbooks'):
        os.makedirs('./orderbooks', exist_ok=False)
        if args.log: print("               Created the Orderbook directory!")
    if not os.path.exists('config.json'):
        configlist = []
        now = get_time(True)
        item = {"time": now,
                "mybudget": "STRING",
                "mybalance": "0.00000000",
                "advice": "0.00069",
                }
        configlist.append(item)
        with open("config.json", 'w') as configfile:  # open file in write mode
            json.dump(configlist, configfile)
        if args.log: print("               Created the config.json")

    update_progress(0 / 100.0)
    while True:
        try:
            fetch_markets = polo.fetch_markets()
            with open("json/poloniex_markets.json", "w") as outfile:
                json.dump(fetch_markets, outfile, sort_keys=True, separators=(',', ':'))
            if show or args.log: print(C.disable, "{:>30}".format('poloniex_markets.json'), '    saved', C.rst)
            update_progress(10 / 100.0)

            polo_currencies = polo.fetch_currencies()
            with open("json/poloniex_currencies.json", "w") as outfile:
                json.dump(polo_currencies, outfile, sort_keys=True, separators=(',', ':'))
            if show or args.log: print(C.disable, "{:>30}".format(' poloniex_currencies.json'), '    saved', C.rst)
            update_progress(20 / 100.0)

            polo_fetch = polo.fetch_balance()
            with open("json/poloniex_balances_full.json", "w") as outfile:
                json.dump(polo_fetch, outfile, sort_keys=True, separators=(',', ':'))
            if show or args.log: print(C.disable, "{:>30}".format(' poloniex_balances_full.json'), '    saved', C.rst)
            update_progress(30 / 100.0)

            polo_tickers = polo.fetch_tickers()
            with open("json/poloniex_tickers.json", "w") as outfile:
                json.dump(polo_tickers, outfile, sort_keys=True, separators=(',', ':'))
            if show or args.log: print(C.disable, "{:>30}".format(' poloniex_tickers.json'), '    saved', C.rst)
            update_progress(40 / 100.0)

            with open('json/poloniex_balances_full.json', 'r') as openfile:  # Opening JSON file
                balance_full = json.load(openfile)['info'][0]['balances']  # Reading from json file
            update_progress(50 / 100.0)
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
    update_progress(90 / 100.0)
    res = dict()  # create new dictionary to fill
    for sub in myBalances:
        key, *val = sub.split()  # split() for key
        res[key] = val  # packing value list
    with open("json/poloniex_balances.json", "w") as outfile:
        json.dump(res, outfile, sort_keys=True, separators=(',', ':'))
    if show or args.log: print(C.disable, "{:>30}".format(' poloniex_balances.json'), '    saved', C.rst)
    update_progress(100 / 100.0)
    if show:
        menu()
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
    if args.log:
        print("           All the live_Markets")
        print(live_market)
    print('   All live markets as json/poloniex_live_market.txt  saved')
    Btc_Markets = []
    for x in sorted(live_market):
        if "_BTC" in x:
            Btc_Markets.append(x)
    with open("json/poloniex_Btc_Markets.txt", 'w') as outfile:  # open file in write mode
        for pair in Btc_Markets:
            outfile.write("%s\n" % pair)  # write each item on a new line
    if args.log:
        print("           All the Btc_Markets")
        print(Btc_Markets)
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
    if args.log:
        print(ListedCoins)
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
        if args.log:
            print(PoloniexCoinlist)
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
    if show or args.log:
        print("{:>20}".format("BTC"), "  ====>",  "{:>14}".format("₿ %.8f" % btcfree))
    counter = 0
    max = len(Coins) - 1
    while counter <= max:
        x = Coins[counter]
        if x in balances:
            pair = str(x + "/BTC")
            LastPrice = float((tickers[pair]['last']))
            amount = balances.get(x)[0]
            altTotal = float(LastPrice) * float(amount)
            if show or args.log:
                print(f"{x:>20}", "  ====>", "{:>14}".format("₿ %.8f" % altTotal))
            wallet = wallet + altTotal
        else:
            altTotal = float(0.0)
            wallet = wallet + altTotal
        counter = counter + 1
    if show or args.log:
        print("        total btc available:   ₿ %.8f" % wallet)
    with open('config.json', 'r') as configfile:
        loadconfig = json.load(configfile)
    loadconfig[0]["mybalance"] = "%.8f" % wallet
    with open('config.json','w') as jsonfile:
        json.dump(loadconfig, jsonfile, indent=4)
    if show:
        menu()


def advice():
    PoloniexCoins = []
    with open("json/poloniex_btc_pairs.txt", 'r') as openBtcpair:  # Get list from a local file
        for line in openBtcpair:  # remove linebreak from a current name
            x = line[:-1]
            PoloniexCoins.append(x)
    max_index = len(PoloniexCoins) - 1
    with open('config.json', 'r') as configfile:
        loadconfig = json.load(configfile)
    btc_balance = float(loadconfig[0]["mybalance"])
    mybudget = float(loadconfig[0]["mybudget"])
    input_advice = round((btc_balance * 0.8) / (max_index + 1), 6)
    budg = str("%.6f" % mybudget)
    print("             Poloniex has   : ", max_index + 1, "Bitcoin markets")
    print("             BTC available  :  ₿ %.8f" % btc_balance)
    print("              budget input  :  ₿ " + budg[:6] + C.disable + budg[6:], C.rst)

    loadconfig[0]["advice"] = input_advice
    with open('config.json','w') as jsonfile:
        json.dump(loadconfig, jsonfile, indent=4) # you decide the indentation level


def collect_orders(show=False):
    global item, orderPrint
    market = 'LIMIT'  # LIMIT_MAKER - MARKET
    PoloniexCoins = []
    with open("json/poloniex_btc_pairs.txt", 'r') as openBtcpair:  # Get list from a local file
        for line in openBtcpair:  # remove linebreak from a current name
            x = line[:-1]
            PoloniexCoins.append(x)
    with open('json/poloniex_balances.json', 'r') as openBalances:  # Reading from json file
        balances = json.load(openBalances)
    with open('json/poloniex_tickers.json', 'r') as openTickers:
        tickers = json.load(openTickers)
    with open('config.json', 'r') as configfile:
        loadconfig = json.load(configfile)
    budget = loadconfig[0]["mybudget"]
    counter = 0
    max_index = len(PoloniexCoins) - 1
    progress = ProgressBar(max_index, fmt=ProgressBar.FULL)
    orderlist = []
    exclude = [name.upper() for name in args.exclude]

    while counter <= max_index:  # while = loop through PoloniexCoins List until max_index
        progress()
        AltCoin = PoloniexCoins[counter]  # Every loop change variable AltCoin
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
        if args.log:
            print("         latest prices Sell(ask)", Ask, "Buy(bid)", Bid)
        while True:  # Check if the AltWorth is Higher or Lower than Budget (script-input)
            try:
                if float(AltWorth) >= float(budget):  # Higher = SELL
                    side = "SELL"
                    OrderWorth = float(AltWorth) - float(budget)  # Calculate how much to sell in BTC
                    AltAmount = float(OrderWorth) / float(Bid)  # Calculate how much AltCoins to Sell
                    List = Bids
                    break  # stop if loop
                else:
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
                    if args.log:
                        print(C.disable, "  [", "{:<7}".format(AltCoin), "Order too Small ]", C.rst)
                        break

                i = 0
                if args.log:
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
                    if args.log:
                        print("  | %.8f" % askAvailable, "==> ₿ %.8f" % askPrice, "- ₿ %.8f" % bidPrice,
                              " <== %.8f" % bidAvailable, " |")
                    i = i + 1

                if args.log:
                    print("   ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾ ")
                    print('             orderbooks/' + pair + '.json               saved')
                    print("{:19}".format("   got %.4f" % AltTotal, "@price"), "{:11}".format(pair), headline)
                    print("               " + "{:<7}".format(AltCoin) + " are Worth: ₿ %.8f" % AltWorth)

                if AltCoin in exclude:
                    print(C.F.cyn, "  ", "{:<7}".format(AltCoin), "Exclude", C.rst)
                elif MinOrder < OrderWorth:
                    if side == "BUY":
                        print(C.F.rd, "  ", "{:<7}".format(AltCoin), " Buy = ₿ %.8f" % OrderWorth, C.rst)
                    else:
                        print(C.F.gr, "  ", "{:<7}".format(AltCoin), "Sell = ₿ %.8f" % OrderWorth, C.rst)
                break
            except IndexError:
                print(" Orderbook smaller than 5")
        if AltCoin in exclude:
            side = "exclude"
        while True:  # 5 get the orderbook of the coinpair (All Sell & Buy Orders)
            try:
                if MinOrder > OrderWorth:
                    break
                else:
                    order = float(0.0)
                    i = 0
                    price = 0.0
                    if args.log:
                        print("   _________________", side, "OrderBook ___________________ ")
                    while order <= OrderWorth:
                        try:
                            price = float(List[i][0])
                            amount = float(List[i][1])
                            available = (price * amount)
                            order = order + available
                            if args.log:
                                print("  |   (", i + 1, ") %.8f" % available, AltCoin, "    for    ₿ %.8f" % price,
                                      "   |")
                            i = i + 1
                        except IndexError:
                            break
                    total = AltAmount * price
                    if args.log:
                        print("   ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾ ")
                        print("        Order will use ", i, " available orders")
                        print("")
                        print("             amount:   %.8f" % AltAmount, AltCoin)
                        print("              price: ₿ %.8f" % price)
                        print("              total: ₿ %.8f" % total)
                    now = get_time(True)
                    try:
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
                        if args.log:
                            print(item)
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

        progress.current += 1
        sleep(0.001)
        counter = counter + 1
    progress.done()
    with open("json/orderlist.json", "w") as orderlistFile:
        json.dump(orderlist, orderlistFile, separators=(',', ':'))
    print('             json/orderlist.json                      saved')
    with open("json/prev_order.json", "a") as prevOrderFile:
        json.dump(orderlist, prevOrderFile)
    if show:
        menu()


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
    print("            orders: ", max_index + 1, "     list created", lagg, "seconds ago")
    print("{:>9}".format("| Order"), "{:<22}".format("|       Amount "), "{:>12}".format("|    Price   "),
          "{:>15}".format("|   Total     |"), " status")
    incomplete = []
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
                        status = "| "+C.F.rd+"Complete"+C.rst+"  |"
                        trade_amount = "{:>16}".format(" %.8f" % amount)
                    elif side == "SELL":
                        polo.create_order(symbol, tradetype, side, amount, price)
                        status =  "| "+C.F.gr+"Complete"+C.rst+"  |"
                        trade_amount = "{:>16}".format(" %.8f" % quantity)
                    elif side == "exclude":
                        status =  "| "+C.F.cyn+"exclude"+C.rst+"  |"
                except ValueError:
                    status = "INCOMPLETE"
                    incomplete.append(orders[nr])
                    trade_amount = "{:>16}".format(" %.8f" % amount)
        elif side == "exclude":
            status =  "| "+C.F.cyn+"exclude"+C.rst+"  |"
        else:
            status = "{:>9}".format("---")
            trade_amount = "{:>16}".format(" %.8f" % amount)

        print(f"{side:>8}",
              trade_amount,
              f"{alt:<7}",
              " %.8f" % price,
              "  %.8f" % total,
              status)
        time.sleep(0.1)
        nr = nr + 1

    if place:
        item = {"symbol": "symbol",
                "type": "type",
                "side": "side",
                "AltAmount": "AltAmount",
                "quantity": "quantity",
                "price": "price",
                "total": "total",
                "alt": "alt",
                "time": get_time()}
        with open("json/orderlist.json", "w") as orderlistFile:
                if not incomplete:
                    json.dump(item, orderlistFile, separators=(',', ':'))
                else:
                    json.dump(incomplete, orderlistFile, separators=(',', ':'))
        completed()
    else:
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


def update_progress(progress):
    barLength = 33  ## A value at 1 or bigger represents 100%
    status = ""
    if isinstance(progress, int):
        progress = float(progress)
    if not isinstance(progress, float):
        progress = 0
        status = "error: progress var must be float\r\n"
    if progress < 0:
        progress = 0
        status = "Halt...\r\n"
    if progress >= 1:
        progress = 1
        status = "Done...\r\n"
    block = int(round(barLength * progress))
    text = "\r  Updating: [{0}] {1}% {2}".format("#" * block + "-" * (barLength - block), progress * 100, status)
    sys.stdout.write(text)
    sys.stdout.flush()


def menu():
    print('            |‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾|')
    print('            |  1: start bot (automatic)     |')
    print('            |  2: update markets            |')
    print('            |  3: total_balance             |')
    print('            |  4: collect_orders            |')
    print('            |  5: order_list                |')
    print('            |  6: Place the Order           |')
    print('            |                               |')
    print('            |  9: extra  option             |')
    print('            |  0: exit tradebot             |')
    print('             ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾ ')
    menuchoices = {
        1: start_bot,
        2: get_update,
        3: total_balance,
        4: collect_orders,
        5: order_list,
        6: order_list,
        9: options,
        0: exit_tradebot
    }
    print(' ')
    try:
        menuitem = int(input('                 Please input menu choice: '))
        if menuitem < 9:
            if  menuitem == 2 or menuitem == 3 or menuitem == 4 or menuitem == 6:
                menuchoices[menuitem](True)
            else:
                menuchoices[menuitem]()
        else:
            print(' ')
            print("          Something went wrong! Call the police!")
            print(' ')
            menu()
    except (KeyError, ValueError):
        print("          Something went wrong! Enter an option number!")
        menu()


def options():
    print('            |‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾|')
    print('            |  All functions                |')
    print('            |  1: getUpdate                 |')
    print('            |  2: market_list               |')
    print('            |  3: listed                    |')
    print('            |  4: makePoloniexCoins         |')
    print('            |  5: get_open_orders           |')
    print('            |  6: Color test                |')
    print('             ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾ ')
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
    if menuitem < 10:
        if menuitem == 5 or menuitem == 8 or menuitem == 7:
            options_choices[menuitem](True)
        else:
            options_choices[menuitem]()
    else:
        print(' ')
        print("          Something went wrong! Call the police!")
        print(' ')
        menu()


def start_bot():
    get_update(True)
    market_list()
    collect_orders()
    order_list(True)


if __name__ == "__main__":

    logo()
    welcome()
    get_update()
    with open('config.json', 'r') as configfile:
        loadconfig = json.load(configfile)
    budget = float(loadconfig[0]["mybudget"])
    get_inputs()

    if args.run:
        start_bot()
    else:
        advice()
        advice = loadconfig[0]["advice"]
        adv = str("%.6f" % advice)
        if budget < advice:
            print("          advice 80% of btc :", C.F.gr,
                  "₿", adv[:6] + C.rst + C.disable + adv[6:], C.rst)
        else:
            print("          advice 80% of btc :", C.F.rd,
                  "₿", adv[:6] + C.rst + C.disable + adv[6:], C.rst)
        menu()
