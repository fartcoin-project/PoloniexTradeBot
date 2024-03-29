#! python3
# coding=utf-8
from __future__ import print_function
import os
import re
import sys
import ccxt
import json
import time
import argparse
import tradebot_config
from time import sleep
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
parser.add_argument("-run", action=argparse.BooleanOptionalAction,
                    help="run the bot without menu, best to input with --budget ")
parser.add_argument("-log", action=argparse.BooleanOptionalAction,
                    help="extra log print in console")
parser.add_argument("--budget", required=False,
                    help="for ₿ 0.0001 Budget input '--budget 0.0001' ")
parser.add_argument("--sell", action=argparse.BooleanOptionalAction,
                    help=" (Sell only) or (Buy only)")
parser.add_argument("--excl", nargs='*', required=False,
                    help="Exclude coins from bot, MUST BE LAST argument")

args = parser.parse_args()
argv = sys.argv[1:]


def get_inputs(update=False):
    while True:  # First check for user BTC Value input
        try:
            with open('config.json', 'r') as bot_configfile:
                load_botconfig = json.load(bot_configfile)
                config_budget = float(load_botconfig["budget"])

            if update is True:
                print(C.F.lbl, "{:<59}".format(
                    "         your current --budget: ₿ {:<15}".format("%.8f" % float(load_botconfig["budget"]))), C.r)
                print("                  minimum order  ₿ 0.0001 ")
                budget_input = float(input('                          Input: ₿ '))
                load_botconfig["budget"] = budget_input
                with open('config.json', 'w') as jsonfile:
                    json.dump(load_botconfig, jsonfile, indent=4)
            elif args.budget is not None:
                budget_arg = f'{args.budget}'
                budget_in = float(budget_arg)
                my_budget = "%.5f" % budget_in
                print("{:<59}".format("             __________________________________ "))
                print("{:<59}".format("            |   budget is given by argument    | "))
                print("{:<59}".format("            |     " + C.F.lbl + " --budget {:<15}".format(my_budget) + C.r + "    | "))
                print("{:<59}".format("             ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾ "))
                load_botconfig["budget"] = float(my_budget)
                with open('config.json', 'w') as jsonfile:
                    json.dump(load_botconfig, jsonfile, indent=4)
                if args.run is True:
                    break
            else:
                if config_budget != 0.0:
                    print("{:<59}".format("             __________________________________ "))
                    print("{:<59}".format("            |   budget found in config.json    | "))
                    print("{:<59}".format(
                        "            |    " + C.F.lbl + "  --budget {:<15}".format(config_budget) + C.r + "    | "))
                    print("{:<59}".format("             ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾ "))
                    if args.run is True: break
                else:
                    print("                        budget = ₿ 0.0    ")
                    print("                  minimum order  ₿ 0.0001 ")
                    budget_input = float(input('                          Input: ₿ '))
                    load_botconfig["budget"] = budget_input
                with open('config.json', 'w') as jsonfile:
                    json.dump(load_botconfig, jsonfile, indent=4)
            if args.log is True:
                print("{:>23}".format("-log") + C.F.yel +"   Show Full Log" + C.r)
            if args.sell is True:
                print("{:>23}".format("--sell") + C.F.yel +"   Sell Only on" + C.r)
            if args.sell is False:
                print("{:>23}".format("--no-sell") + C.F.yel + "   Buy Only " + C.r)
            if args.excl is not None:
                exclude_list = args.excl
                exclude = [name.upper() for name in exclude_list]
                load_botconfig["exclude"] = exclude
                with open('config.json', 'w') as jsonfile:
                    json.dump(load_botconfig, jsonfile, indent=4)
            if load_botconfig["exclude"]:
                exclude_list = load_botconfig["exclude"]
                print("{:>23}".format("--excl"), C.F.cyn, exclude_list, C.r)
            if update is True:
                menu()
            break
        except(ValueError, IndexError):  # Print an Exception (error) if there is no input
            print("Print an Exception (error)")
            break


def change_exclude_list():
    with open('config.json', 'r') as bot_configfile:
        load_botconfig = json.load(bot_configfile)
    exclude_coins = load_botconfig["exclude"]
    print("     You can change or input the coins to exclude from the bot")
    print("{:>23}".format("--excl"), C.F.cyn, exclude_coins, C.r)
    change_exclude_input = input("  Exclude separated by space: ")
    change_exclude_list = change_exclude_input.split(" ")
    exclude = [name.upper() for name in change_exclude_list]
    load_botconfig["exclude"] = exclude
    with open('config.json', 'w') as jsonfile:
        json.dump(load_botconfig, jsonfile, indent=4)
    print("   New exclude list is saved.\n   This is the new exclude list:")
    print("{:>23}".format("--excl"), C.F.cyn, exclude, C.r)
    menu()


class C:
    r = '\033[0;0m'
    b = '\033[1;01m'
    d = '\033[1;02m'
    u = '\033[1;04m'
    o = '\033[1;07m'
    s = '\033[1;09m'
    i = '\033[1;08m'

    class F:
        blk = '\033[1;30m'
        rd = '\033[1;31m'
        gr = '\033[1;32m'
        orng = '\033[1;33m'
        bl = '\033[1;34m'
        prpl = '\033[1;35m'
        cyn = '\033[1;36m'
        gry = '\033[1;37m'
        dgry = '\033[1;90m'
        lrd = '\033[1;91m'
        lgr = '\033[1;92m'
        yel = '\033[1;93m'
        lbl = '\033[1;94m'
        pnk = '\033[1;95m'
        lcyn = '\033[1;96m'

    class B:
        blk = '\033[1;40m'
        rd = '\033[1;41m'
        gr = '\033[1;42m'
        orng = '\033[1;43m'
        bl = '\033[1;44m'
        prpl = '\033[1;45m'
        cyn = '\033[1;46m'
        lgry = '\033[1;47m'


def print_format_table():
    print(C.B.gr, "testo", C.F.rd, "pesto", C.r)
    print("pesta", C.F.cyn, "pasta", C.r)
    for style in range(8):
        for fg in range(30, 38):
            s1 = ''
            for bg in range(40, 48):
                print_format = ';'.join([str(style), str(fg), str(bg)])
                s1 += '\x1b[%sm %s \x1b[0m' % (print_format, print_format)
            print(s1)
        print('\n')
    options()


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

        arguments = {
            'total': self.total,
            'bar': bar,
            'current': self.current,
            'percent': percent * 100,
            'remaining': remaining
        }
        print('\r' + self.fmt % arguments, file=self.output, end='')

    def done(self):
        self.current = self.total
        self()
        print('', file=self.output)


def update_progress(progress):
    bar_length = 33  # A value at 1 or bigger represents 100%
    update_status = ""
    if isinstance(progress, int):
        progress = float(progress)
    if not isinstance(progress, float):
        progress = 0
        update_status = "error: progress var must be float\r\n"
    if progress < 0:
        progress = 0
        update_status = "Halt...\r\n"
    if progress >= 1:
        progress = 1
        update_status = "Done...\r\n"
    block = int(round(bar_length * progress))
    text = "\r  Updating: [{0}] {1}% {2}".format("#" * block + "-" * (bar_length - block), progress * 100, update_status)
    sys.stdout.write(text)
    sys.stdout.flush()


def logo():
    print(C.F.gr, "        ____       _             _ ")
    print("       |  _ \ ___ | | ___  _ __ (_) _____  __ ")
    print("       | |_) / _ \| |/ _ \| '_ \| |/ _ \ \/ / ")
    print("       |  __/ (_) | | (_) | | | | |  __/>  < ")
    print("       |_|   \___/|_|\___/|_| |_|_|\___/_/\_\ ")
    print("               _____              _      _           _ ")
    print("              |_   _| __ __ _  __| | ___| |__   ___ | |_ ")
    print("                | || '__/ _` |/ _` |/ _ \ '_ \ / _ \| __| ")
    print("                | || | | (_| | (_| |  __/ |_) | (_) | |_ ")
    print("                |_||_|  \__,_|\__,_|\___|_.__/ \___/ \__| ")
    print("                                 Connected to Poloniex.com  ", C.r)


def welcome():
    print("\n\n                  pip install --upgrade ccxt")
    print(C.F.gr, '   please use referral:', C.F.cyn, 'F8GSBSS5', C.r, '            ')


def completed():
    print('             referral code:', C.F.cyn, 'F8GSBSS5', C.r)
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
    print("         ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾ ")
    exit_tradebot()


def exit_tradebot(good_exit=False):
    if good_exit:
        print(C.F.bl, "   ______  __ __   ____  ____   __  _      __ __   ___   __ __  ")
        print("   |      ||  |  | /    ||    \ |  |/ ]    |  |  | /   \ |  |  | ")
        print("   |      ||  |  ||  o  ||  _  ||  ' /     |  |  ||     ||  |  | ")
        print("   |_|  |_||  _  ||     ||  |  ||    \     |  ~  ||  O  ||  |  | ")
        print("     |  |  |  |  ||  _  ||  |  ||     \    |___, ||     ||  :  | ")
        print("     |  |  |  |  ||  |  ||  |  ||  .  |    |     ||     ||     | ")
        print("     |__|  |__|__||__|__||__|__||__|\_|    |____/  \___/  \__,_| ", C.r)
        print('       please use referral code:', C.F.cyn, 'F8GSBSS5', C.r)
    else:
        print("sorry please try again")
    exit(1)


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


def options():
    help_menu()
    print('            |‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾|')
    print('            |  Extra functions              |')
    print('            |  1: get_open_orders           |')
    print('            |  2: Color test                |')
    print('            |  0: back                      |')
    print('             ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾ ')
    options_choices = {

        1: get_open_orders,
        2: print_format_table,
        0: menu
    }
    print(' ')
    menuitem = int(input('                 Please choose option: '))
    if menuitem < 10:
        options_choices[menuitem]()
    else:
        print(' ')
        print("          Something went wrong! Call the police!")
        print(' ')
        menu()


def help_menu():
    print("{:<59}".format("                     -h --HELP MENU                    "))
    print("{:<59}".format("    |‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾|"))
    print("{:<59}".format("    |                 tradebot.py  arguments   "), "|")
    print("{:<59}".format("    | -run             => no input, best with --budget"), "|")
    print("{:<59}".format("    | -log             => extra log print in console"), "|")
    print("{:<59}".format("    | --budget         =>  --₿udget 0.0001  "), "|")
    print("{:<59}".format("    | --sell --no-sell => Input the coins to exclude"), "|")
    print("{:<59}".format("    | --excl [coin ..] => Exclude coins from bot, "), "|")
    print("{:<59}".format("    |                      MUST BE LAST ARGUMENT    "), "|")
    print("{:<59}".format("    |                    --excl without coins = reset  "), "|")
    print("{:<59}".format("     ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾ "))
    print(" ")


def are_you_sure():
    print("          ! tradebot will complete the BUY and Sell orders !")
    try:
        assurance = str(input("                        Are you sure? (y/n) "))
        if assurance == "y" or assurance == "Y":
            start_bot()
        elif assurance == "n" or assurance == "N":
            menu()
        else:
            print("          Something went wrong! Are you sure? (y/n) ")
    except (KeyError, ValueError):
        print("          Something went pretty wrong! ")
        exit(1)


def get_update(show=False):  # 1
    print("")
    update_progress(0 / 100.0)
    if not os.path.exists('./json'):
        os.makedirs('./json', exist_ok=False)
        if args.log:
            print("               Created the Json directory!")
    if not os.path.exists('./orderbooks'):
        os.makedirs('./orderbooks', exist_ok=False)
        if args.log:
            print("               Created the Orderbook directory!")
    if not os.path.exists('config.json'):
        now = get_time(True)
        new_config_item = dict(time=now, budget=0.0, balance=0.00000000, advice="0.0005", exclude=[])
        with open("config.json", 'w') as load_configfile:  # open file in write mode
            json.dump(new_config_item, load_configfile, indent=4)
        print("            Created the default ₿ 0.0 config.json  ")

    while True:
        try:
            fetch_markets = polo.fetch_markets()
            with open("json/poloniex_markets.json", "w") as outfile:
                json.dump(fetch_markets, outfile, sort_keys=True, indent=4)
            if show or args.log:
                print(C.d, "{:>30}".format('poloniex_markets.json'), '    saved', C.r)
            update_progress(10 / 100.0)

            polo_currencies = polo.fetch_currencies()
            with open("json/poloniex_currencies.json", "w") as outfile:
                json.dump(polo_currencies, outfile, sort_keys=True, indent=4)
            if show or args.log:
                print(C.d, "{:>30}".format(' poloniex_currencies.json'), '    saved', C.r)
            update_progress(20 / 100.0)

            polo_fetch = polo.fetch_balance()
            with open("json/poloniex_balances_full.json", "w") as outfile:
                json.dump(polo_fetch, outfile, sort_keys=True, indent=4)
            if show or args.log:
                print(C.d, "{:>30}".format(' poloniex_balances_full.json'), '    saved', C.r)
            update_progress(30 / 100.0)

            polo_tickers = polo.fetch_tickers()
            with open("json/poloniex_tickers.json", "w") as outfile:
                json.dump(polo_tickers, outfile, sort_keys=True, indent=4)
            if show or args.log:
                print(C.d, "{:>30}".format(' poloniex_tickers.json'), '    saved', C.r)
            update_progress(40 / 100.0)

            with open('json/poloniex_balances_full.json', 'r') as openfile:  # Opening JSON file
                balance_full = json.load(openfile)['info'][0]['balances']  # Reading from json file
            update_progress(50 / 100.0)
            break
        except TimeoutError:
            print("             An TimeoutError occurred, please retry")
            exit(1)

    my_balances = []
    counter = 0
    max_index = len(balance_full) - 1
    while counter <= max_index:
        currency = balance_full[counter]['currency']
        available = balance_full[counter]['available']
        my_balances.append(currency + ' ' + available)
        counter = counter + 1
    update_progress(60 / 100.0)
    res = dict()  # create new dictionary to fill
    for sub in my_balances:
        key, *val = sub.split()  # split() for key
        res[key] = val  # packing value list
    with open("json/poloniex_balances.json", "w") as outfile:
        json.dump(res, outfile, sort_keys=True, indent=4)
    if show or args.log:
        print(C.d, "{:>30}".format(' poloniex_balances.json'), '    saved', C.r)
    update_progress(70 / 100.0)
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
        market_id = json_object[counter]['id']
        active = json_object[counter]['active']
        if active is True:
            live_market.append(market_id)
        counter = counter + 1
    with open("json/poloniex_live_market.txt", 'w') as outfile:  # open file in write mode
        for market in live_market:
            outfile.write("%s\n" % market)  # write each item on a new line
    if args.log:
        print("           All the live_Markets")
        print(live_market)
        print('   All live markets as json/poloniex_live_market.txt  saved')
    else:
        update_progress(80 / 100.0)
    btc_market_list = []
    for x in sorted(live_market):
        if "_BTC" in x:
            btc_market_list.append(x)
    with open("json/poloniex_Btc_Markets.txt", 'w') as outfile:  # open file in write mode
        for pair in btc_market_list:
            outfile.write("%s\n" % pair)  # write each item on a new line
    if args.log:
        print("           All the btc_markets")
        print(btc_market_list)
        print('   All _BTC markets as json/poloniex_Btc_Markets.txt  saved')
    else:
        update_progress(90 / 100.0)
    listed()


def listed():  # 3
    with open('json/poloniex_currencies.json', 'r') as openfile:  # Opening JSON file
        json_object = json.load(openfile)  # Reading from json file
    key_list = json_object.keys()
    print(key_list)
    listed_coins = []

    for x in sorted(key_list):
        x_id = json_object[x]['id']
        delisted = json_object[x]['info'][0][x_id]['delisted']
        if delisted is False:
            listed_coins.append(x)

    with open("json/poloniex_ListedCoins.txt", 'w') as outfile:  # open file in write mode
        for coins in listed_coins:
            outfile.write("%s\n" % coins)  # write each item on a new line
    if args.log:
        print(listed_coins)
        print('   All listed coins as json/poloniex_ListedCoins.txt  saved')
    else:
        update_progress(90 / 100.0)
    make_poloniex_coins()


def make_poloniex_coins():  # 4
    btc_markets = []  # empty list to read list from a file
    with open("json/poloniex_Btc_Markets.txt", 'r') as outfile:
        for line in outfile:
            x = line[:-1]  # remove linebreak from a current name
            btc_markets.append(x)  # add current item to the list

    listed_coins = []  # empty list to read list from a file
    with open("json/poloniex_ListedCoins.txt", 'r') as outfile2:
        for line2 in outfile2:
            y = line2[:-1]  # remove linebreak from a current name
            listed_coins.append(y)  # add current item to the list

    poloniex_coinlist = []
    counter = 0
    max_index = len(listed_coins) - 1
    while counter <= max_index:
        coin = listed_coins[counter]
        symbol = coin + "_BTC"
        for x in btc_markets:
            if symbol == x:
                poloniex_coinlist.append(coin)
        counter = counter + 1

    with open("json/poloniex_btc_pairs.txt", 'w') as outfile:  # open file in write mode
        for coin in poloniex_coinlist:
            outfile.write("%s\n" % coin)  # write each item on a new line
        if args.log:
            print(poloniex_coinlist)
            print('        BTC markets as json/poloniex_btc_pairs.txt  saved')
        else:
            update_progress(100 / 100.0)
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
    coins = []
    with open("json/poloniex_btc_pairs.txt", 'r') as openBtcpair:  # Get list from a local file
        for line in openBtcpair:  # remove linebreak from a current name
            x = line[:-1]
            coins.append(x)
    with open('json/poloniex_balances.json', 'r') as openBalances:  # Reading from json file
        balances = json.load(openBalances)
    with open('json/poloniex_tickers.json', 'r') as openTickers:
        tickers = json.load(openTickers)
    wallet = 0.0
    btcfree = float(balances.get("BTC")[0])
    wallet = wallet + btcfree
    if show or args.log:
        print("{:>20}".format("BTC"), "  ====>", "{:>14}".format("₿ %.8f" % btcfree))
    counter = 0
    loop_length = len(coins) - 1
    while counter <= loop_length:
        x = coins[counter]
        if x in balances:
            pair = str(x + "/BTC")
            last_price = float((tickers[pair]['last']))
            amount = balances.get(x)[0]
            alt_total = float(last_price) * float(amount)
            if show or args.log:
                print(f"{x:>20}", "  ====>", "{:>14}".format("₿ %.8f" % alt_total))
            wallet = wallet + alt_total
        else:
            alt_total = float(0.0)
            wallet = wallet + alt_total
        counter = counter + 1
    if show or args.log:
        print("        total btc available:   ₿ %.8f" % wallet)
    with open('config.json', 'r') as balance_configfile:
        load_wallet_config = json.load(balance_configfile)
    load_wallet_config["balance"] = "%.8f" % wallet
    with open('config.json', 'w') as jsonfile:
        json.dump(load_wallet_config, jsonfile, indent=4)
    if show:
        menu()


def advice():
    poloniex_coins = []
    with open("json/poloniex_btc_pairs.txt", 'r') as openBtcpair:  # Get list from a local file
        for line in openBtcpair:  # remove linebreak from a current name
            x = line[:-1]
            poloniex_coins.append(x)
    max_index = len(poloniex_coins) - 1
    with open('config.json', 'r') as configfile:
        load_advice_config = json.load(configfile)
    btc_balance = float(load_advice_config["balance"])
    mybudget = float(load_advice_config["budget"])
    if max_index == -1: max_index = 0
    input_advice = round((btc_balance * 0.8) / (max_index + 1), 6)
    print("         ", max_index + 1, "Bitcoin markets")
    print("               BTC available  :  ₿ %.8f" % btc_balance)
    adv = str("%.6f" % input_advice)
    if mybudget < input_advice:
        print("            advice 80% of btc :", C.F.gr,
              "₿", adv[:6] + C.r + C.d + adv[6:], C.r)
    else:
        print("            advice 80% of btc :  ₿ " + C.F.rd +
              adv[:6] + C.r + C.d + adv[6:], C.r)
    load_advice_config["advice"] = input_advice
    with open('config.json', 'w') as jsonfile:
        json.dump(load_advice_config, jsonfile, indent=4)  # you decide the indentation level


def collect_orders(show=False):
    global item, orderPrint, price
    market = 'LIMIT'  # LIMIT_MAKER - MARKET
    poloniex_coins = []
    with open("json/poloniex_btc_pairs.txt", 'r') as openBtcpair:  # Get price_list from a local file
        for line in openBtcpair:  # remove linebreak from a current name
            x = line[:-1]
            poloniex_coins.append(x)
    with open('json/poloniex_balances.json', 'r') as openBalances:  # Reading from json file
        balances = json.load(openBalances)
    with open('json/poloniex_tickers.json', 'r') as openTickers:
        tickers = json.load(openTickers)
    with open('config.json', 'r') as configfile:
        load_config_coinlist = json.load(configfile)
    budget_input = load_config_coinlist["budget"]
    counter = 0
    max_index = len(poloniex_coins) - 1
    progress = ProgressBar(len(poloniex_coins), fmt=ProgressBar.FULL)
    orders_list = []
    while counter <= max_index:  # while = loop through poloniex_coins list until max_index
        progress()
        progress.current += 1
        alt_coin = poloniex_coins[counter]  # Every loop change variable alt_coin
        symbol = str(alt_coin + "/BTC")
        pair = str(alt_coin + "_BTC")
        if alt_coin in balances:
            jv1 = balances.get(alt_coin)[0]
            alt_total = float(jv1)  # Get your amount of the altcoin
        else:
            alt_total = float(0.0)
        last_price = float((tickers[symbol]['last']))
        alt_worth = float(last_price) * float(alt_total)
        headline = str("  ₿ %.8f" % last_price)
        fetch_orderbook = polo.fetch_order_book(pair, 5)
        with open("orderbooks/" + pair + ".json", "w") as outfile:
            json.dump(fetch_orderbook, outfile, indent=4)
        with open("orderbooks/" + pair + ".json", 'r') as openfile:
            orderbook = json.load(openfile)  # Reading from json file
        asks = orderbook['asks']  # [[Price, Amount],[...]]
        ask = asks[0][0]  # Collect latest Sell(ask) prices
        bids = orderbook['bids']  # [[Amount, Price],[...]]
        bid = bids[0][0]  # Collect latest Buy (bid) prices
        if args.log:
            print("         latest prices Sell(ask)", ask, "Buy(bid)", bid)
        while True:  # Check if the alt_worth is Higher or Lower than Budget (script-input)
            try:
                if float(alt_worth) >= float(budget_input):  # Higher = SELL
                    if args.sell is False or alt_coin in exclude_list:
                        side = "exclude"
                    else:
                        side = "SELL"
                    order_worth = float(alt_worth) - float(budget_input)  # Calculate how much to sell in BTC
                    alt_amount = float(order_worth) / float(bid)  # Calculate how much AltCoins to Sell
                    price_list = bids
                    break  # stop if loop
                else:
                    if args.sell is True or alt_coin in exclude_list:
                        side = "exclude"
                    else:
                        side = "BUY"
                    order_worth = float(budget_input) - float(alt_worth)  # Calculate how much to buy in BTC
                    alt_amount = float(order_worth) / float(ask)  # Calculate how much AltCoins to Buy
                    price_list = asks
                    break  # stop else loop

            except ValueError:
                order_worth = 0.000001
                alt_amount = 0.0
                side = "ERROR"
                price_list = []
                orderPrint = "  The Orderbook does not work, Maybe no orders."
                break
        while True:
            try:
                min_order = 0.0001  # Minimal order worth in BTC = Poloniex Trading Rule
                if min_order > order_worth:  # Compare min_order with AltSellWorth
                    if args.log:
                        print(C.d, "  [", "{:<7}".format(alt_coin), "Order too Small ]", C.r)
                        break

                i = 0
                if args.log:
                    print("")
                    print("  |‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾", "{:<11}".format(pair), "OrderBook ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾| ")
                    print("  | Amount", "{:<7}".format(alt_coin), "      ₿ Buy  - Sell ₿               ",
                          "{:<7}".format(alt_coin), "|")
                while i <= 4:
                    try:
                        ask_price = float(asks[i][0])
                        ask_amount = float(asks[i][1])
                        ask_available = (ask_price * ask_amount)
                    except IndexError:
                        ask_available = 0
                        ask_price = 0
                    try:
                        bid_price = float(bids[i][0])
                        bid_amount = float(bids[i][1])
                        bid_available = (bid_price * bid_amount)
                    except IndexError:
                        bid_available = 0
                        bid_price = 0
                    if args.log:
                        print("  | %.8f" % ask_available, "==> ₿ %.8f" % ask_price, "- ₿ %.8f" % bid_price,
                              " <== %.8f" % bid_available, " |")
                    i = i + 1

                if args.log:
                    print("   ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾ ")
                    print('             orderbooks/' + pair + '.json               saved')
                    print("{:19}".format("   got %.4f" % alt_total, "@price"), "{:11}".format(pair), headline)
                    print("               " + "{:<7}".format(alt_coin) + " are Worth: ₿ %.8f" % alt_worth)

                if side == "exclude" or alt_coin in exclude_list:
                    print(C.F.cyn, "  ", "{:<7}".format(alt_coin), "Exclude", C.r)
                elif min_order < order_worth:
                    if side == "BUY":
                        print(C.F.rd, "  ", "{:<7}".format(alt_coin), " Buy = ₿ %.8f" % order_worth, C.r)
                    else:
                        print(C.F.gr, "  ", "{:<7}".format(alt_coin), "Sell = ₿ %.8f" % order_worth, C.r)
                break
            except IndexError:
                print(" Orderbook smaller than 5")
        while True:  # 5 get the orderbook of the coinpair (All Sell & Buy Orders)
            try:
                if min_order > order_worth:
                    break
                else:
                    order = float(0.0)
                    i = 0

                    if args.log:
                        print("   _________________", side, "OrderBook ___________________ ")
                    while order <= order_worth:
                        try:
                            price = float(price_list[i][0])
                            amount = float(price_list[i][1])
                            available = (price * amount)
                            order = order + available
                            if args.log:
                                print("  |   (", i + 1, ") %.8f" % available, alt_coin, "    for    ₿ %.8f" % price,
                                      "   |")
                            i = i + 1
                        except IndexError:
                            break
                    total = alt_amount * price
                    if args.log:
                        print("   ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾ ")
                        print("        Order will use ", i, " available orders")
                        print("")
                        print("             amount:   %.8f" % alt_amount, alt_coin)
                        print("              price: ₿ ", price)
                        print("              total: ₿ %.8f" % total)
                    now = get_time(True)
                    try:
                        item = {"symbol": symbol,
                                "type": market,
                                "side": side,
                                "alt_amount": alt_amount,
                                "quantity": alt_amount,
                                "price": price,
                                "total": total,
                                "alt": alt_coin,
                                "time": now
                                }
                        if args.log:
                            print(item)
                        break
                    except ValueError:
                        print("error")

                    finally:
                        orders_list.append(item)
                        break

            # end of try
            except ValueError:
                print("        ---! Can not finish the OrderBook !---")
                print("")
                break
        sleep(0.001)
        counter = counter + 1
    progress.done()
    with open("json/orderlist.json", "w") as orderlistFile:
        json.dump(orders_list, orderlistFile, indent=4)
    print('             json/orders_list.json                      saved')
    with open("json/prev_order.json", "a") as prevOrderFile:
        json.dump(orders_list, prevOrderFile, indent=4)
    if show:
        menu()


def order_list(place=False):
    while True:
        try:
            global status, trade_amount, symbol, side, amount, quantity, price, total, alt, side_color
            with open('json/orderlist.json', 'r') as open_orderlist:  # Opening JSON file
                orders = json.load(open_orderlist)  # Reading from json file
            nr = 0
            max_index = len(orders) - 1
            now = string2list(get_time(True))
            now = [int(i) for i in now]
            then = string2list(orders[len(orders) - 1]['time'])
            then = [int(i) for i in then]
            time_behind = list()
            for i in range(len(now)):
                time_item = now[i] - then[i]
                time_behind.append(time_item)
            lagg = ((time_behind[3] * 60 * 60) + (time_behind[4] * 60) + time_behind[5])
            print("            orders: ", max_index + 1, "     list created", lagg, "seconds ago")
            print("{:>9}".format("| Order"), "{:>22}".format("|    Amount of altcoin "), "{:>12}".format(" |    Price   "),
                  "{:>18}".format(" |     Total     |"), " status  |")
            incomplete = []
            while nr <= max_index:  # while = loop through PoloniexCoins List until max_index
                symbol = orders[nr]['symbol']
                tradetype = orders[nr]['type']
                side = orders[nr]['side']
                amount = orders[nr]['alt_amount']
                quantity = orders[nr]['quantity']
                price = orders[nr]['price']
                total = orders[nr]['total']
                alt = orders[nr]['alt']
                if place:
                    if lagg < 360:
                        try:
                            if side == "exclude" or alt in exclude_list:
                                side_color = C.F.cyn
                                status = "  " + C.F.cyn + "exclude" + C.r + "   "
                                trade_amount = "{:>16}".format("     ---      ")
                            elif side == "BUY":
                                polo.create_order(symbol, tradetype, side, amount, price)
                                side_color = C.F.rd
                                status = "  " + C.F.rd + "Complete" + C.r + "   "
                                trade_amount = "{:>16}".format("%.8f" % amount)
                                time.sleep(0.5)
                            elif side == "SELL":
                                polo.create_order(symbol, tradetype, side, amount, price)
                                side_color = C.F.gr
                                status = "  " + C.F.gr + "Complete" + C.r + "   "
                                trade_amount = "{:>16}".format("%.8f" % quantity)
                                time.sleep(0.5)
                        except:
                            status = "INCOMPLETE"
                            side_color = C.F.prpl
                            incomplete.append(orders[nr])
                            trade_amount = C.r + "{:>16}".format("%.8f" % amount)
                elif side == "exclude" or alt in exclude_list:
                    side_color = C.F.cyn
                    status = C.r + "  " + C.F.cyn + "exclude" + C.r + "   "
                    trade_amount = "{:>16}".format("      ---      ")
                else:
                    side_color = C.F.yel
                    status = "  " + C.F.cyn + "exclude" + C.r + "   "
                    status = "{:>9}".format("Test")
                    trade_amount = "{:>16}".format("%.8f" % amount)
                tot = "  %.8f" % total
                tot_st = tot[:8].replace("0", "*")
                print(side_color,
                      "{:>9}".format(f"{side:>8}"), C.r,
                      "{:>22}".format(trade_amount+f" {alt:<7}"),
                      "{:>12}".format("%.8f" % float(price)),
                      "{:>15}".format(tot_st + C.F.dgry + tot[8:] + C.r).replace("*.", "₿ 0."),
                      side_color, status, C.r)
                time.sleep(0.1)
                nr = nr + 1

            if place:
                order_item = dict(symbol=symbol, type=type, side=side, alt_amount=amount, quantity=quantity,
                                  price=price, total=total, alt=alt, time=get_time())
                if not incomplete:
                    with open("json/orderlist.json", "w") as orderlistFile:
                        json.dump(order_item, orderlistFile, indent=4)
                else:
                    with open("json/orderlist_incomplete.json", "w") as orderlist_incomplete:
                        json.dump(incomplete, orderlist_incomplete, indent=4)
                completed()
            else:
                menu()
        except ConnectionError:
            menu()


def start_bot():
    get_update()
    market_list()
    collect_orders()
    order_list(True)


def menu():
    with open('config.json', 'r') as menu_configfile:
        load_menu_config = json.load(menu_configfile)
    print("\n ")
    print('            |‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾|')
    print("            |     1: start bot " + C.F.gr + " ₿ %.5f" % float(load_menu_config["budget"]) + C.r + "      |")
    print('            |     2: update markets            |')
    print('            |     3: total_balance             |')
    print('            |     4: collect_orders            |')
    print('            |     5: order_list                |')
    print('            |     6: Place the Order           |')
    print('            |     7: Change Exclude List       |')
    print('            |     8: Change Budget             |')
    print('            |     9:      Help                 |')
    print('            |     0: exit tradebot             |')
    print('             ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾ ')
    menuchoices = {
        1: are_you_sure,
        2: get_update,
        3: total_balance,
        4: collect_orders,
        5: order_list,
        6: order_list,
        7: change_exclude_list,
        8: get_inputs,
        9: options,
        0: exit_tradebot,
        11: get_open_orders,
    }
    advice()
    print(' ')
    try:
        menuitem = int(input('                 Please input menu choice: '))
        if menuitem < 20:
            if menuitem == 0 or menuitem == 2 or menuitem == 3 or menuitem == 4 or menuitem == 6 or menuitem == 8:
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


if __name__ == "__main__":

    welcome()
    logo()
    get_update()
    market_list()
    get_inputs()
    with open('config.json', 'r') as configfile:
        loadconfig = json.load(configfile)
    budget = float(loadconfig["budget"])
    exclude_list = loadconfig["exclude"]
    if args.run:
        start_bot()
    menu()
