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
from runtime_paths import app_dir, load_tradebot_config
from api_compat import (
    auth_error_help,
    balances_dict_from_ccxt,
    create_exchange,
    currency_is_tradable,
    is_insufficient_balance_error,
    is_valid_trading_symbol,
    load_btc_available,
    MIN_ORDER_BTC,
    open_text,
    OperationCancelled,
    order_side_for_ccxt,
    order_type_for_ccxt,
)
from budget_helpers import coin_budget_from_config
from quote_config import (
    active_pair_coins,
    ccxt_symbol,
    filter_live_markets,
    format_quote_value,
    is_pair_excluded,
    load_pair_coins,
    load_quote_available,
    market_balance_from_config,
    market_id,
    markets_filename,
    markets_from_config,
    min_order_for_quote,
    pairs_filename,
    portfolio_in_quote,
    primary_quote_from_config,
    quote_from_config,
    suggest_excludes_for_unheld,
)
from time import sleep
from datetime import datetime


class _CliArgs:
    run = None
    log = None
    budget = None
    buy = None
    sell = None
    excl = None


args = _CliArgs()
argv = []
_cancel_check = None
_interactive_menu = True
_test_mode = False


def set_cancel_check(check_fn):
    global _cancel_check
    _cancel_check = check_fn


def set_interactive_menu(enabled):
    """When False, order_list runs once and exits (GUI / automated runs)."""
    global _interactive_menu
    _interactive_menu = bool(enabled)


def is_test_mode():
    """True for GUI trade_mode=test or CLI --no-buy --no-sell."""
    if _test_mode:
        return True
    return getattr(args, "buy", None) is False and args.sell is False


def abort_if_cancelled():
    if _cancel_check and _cancel_check():
        raise OperationCancelled("Emergency stop — cancelled by user")


def gui_sleep(seconds):
    """Sleep in small steps so GUI can interrupt long waits."""
    end = time.time() + float(seconds)
    while time.time() < end:
        abort_if_cancelled()
        time.sleep(min(0.05, end - time.time()))



def parse_cli_args():
    global args, argv
    parser = argparse.ArgumentParser()
    parser.add_argument("-run", action=argparse.BooleanOptionalAction,
                        help="run the bot without menu, best to input with --budget ")
    parser.add_argument("-log", action=argparse.BooleanOptionalAction,
                        help="extra log print in console")
    parser.add_argument("--budget", required=False,
                        help="for ₿ 0.0001 Budget input '--budget 0.0001' ")
    parser.add_argument("--sell", action=argparse.BooleanOptionalAction,
                        help=" (Sell only) or (Buy only)")
    parser.add_argument("--buy", action=argparse.BooleanOptionalAction,
                        help="Enable/disable buys; with --no-sell --no-buy runs TEST dry-run")
    parser.add_argument("--excl", nargs='*', required=False,
                        help="Exclude coins from bot, MUST BE LAST argument")
    args = parser.parse_args()
    argv = sys.argv[1:]


if app_dir() not in sys.path:
    sys.path.insert(0, app_dir())

if sys.platform == "win32":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except (OSError, ValueError):
                pass

tradebot_config = load_tradebot_config()

while True:  # Setup to connect to Poloniex API
    try:
        polo = create_exchange(
            tradebot_config.SECRET_API_KEY,
            tradebot_config.SECRET_API_SECRET,
        )
        break
    except ConnectionError:
        print("Can not connect to Poloniex API")
        exit(1)


def reload_exchange():
    """Reload API credentials from tradebot_config.py (GUI save)."""
    global tradebot_config, polo
    tradebot_config = load_tradebot_config()
    polo = create_exchange(
        tradebot_config.SECRET_API_KEY,
        tradebot_config.SECRET_API_SECRET,
    )
    return polo


def get_inputs(update=False):
    while True:  # First check for user BTC Value input
        try:
            with open_text('config.json', 'r') as bot_configfile:
                load_botconfig = json.load(bot_configfile)
                config_budget = float(load_botconfig["budget"])

            if update is True:
                print(C.F.lbl, "{:<59}".format(
                    "         your current --budget: ₿ {:<15}".format("%.8f" % float(load_botconfig["budget"]))), C.r)
                print("                  budget >= 0 (0 sells down) ")
                budget_input = float(input('                          Input: ₿ '))
                if budget_input < 0:
                    print(C.F.orng, "                  budget must be >= 0 (0 sells down)", C.r)
                    continue
                load_botconfig["budget"] = budget_input
                with open_text('config.json', 'w') as jsonfile:
                    json.dump(load_botconfig, jsonfile, indent=4)
            elif args.budget is not None:
                budget_arg = f'{args.budget}'
                budget_in = float(budget_arg)
                if budget_in < 0:
                    print(C.F.orng, "                  budget must be >= 0 (0 sells down)", C.r)
                    continue
                my_budget = "%.5f" % budget_in
                print("{:<59}".format("             __________________________________ "))
                print("{:<59}".format("            |   budget is given by argument    | "))
                print("{:<59}".format("            |     " + C.F.lbl + " --budget {:<15}".format(my_budget) + C.r + "    | "))
                print("{:<59}".format("             ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾ "))
                load_botconfig["budget"] = float(my_budget)
                with open_text('config.json', 'w') as jsonfile:
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
                    print("                  use 0 to sell down holdings ")
                    budget_input = float(input('                          Input: ₿ '))
                    if budget_input < 0:
                        print(C.F.orng, "                  budget must be >= 0 (0 sells down)", C.r)
                        continue
                    load_botconfig["budget"] = budget_input
                with open_text('config.json', 'w') as jsonfile:
                    json.dump(load_botconfig, jsonfile, indent=4)
            if args.log is True:
                print("{:>23}".format("-log") + C.F.yel +"   Show Full Log" + C.r)
            if is_test_mode():
                print("{:>23}".format("--no-buy --no-sell") + C.F.yel + "   TEST dry-run" + C.r)
            elif args.sell is True:
                print("{:>23}".format("--sell") + C.F.yel +"   Sell Only on" + C.r)
            elif args.sell is False:
                print("{:>23}".format("--no-sell") + C.F.yel + "   Buy Only " + C.r)
            if getattr(args, "buy", None) is True and not is_test_mode():
                print("{:>23}".format("--buy") + C.F.yel + "   Buy enabled" + C.r)
            if args.excl is not None:
                exclude_list = args.excl
                exclude = [name.upper() for name in exclude_list]
                load_botconfig["exclude"] = exclude
                with open_text('config.json', 'w') as jsonfile:
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
    with open_text('config.json', 'r') as bot_configfile:
        load_botconfig = json.load(bot_configfile)
    exclude_coins = load_botconfig["exclude"]
    print("     You can change or input the coins to exclude from the bot")
    print("{:>23}".format("--excl"), C.F.cyn, exclude_coins, C.r)
    change_exclude_input = input("  Exclude separated by space: ")
    change_exclude_list = change_exclude_input.split(" ")
    exclude = [name.upper() for name in change_exclude_list]
    load_botconfig["exclude"] = exclude
    with open_text('config.json', 'w') as jsonfile:
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
    print(C.F.gr, r"        ____       _             _ ")
    print(r"       |  _ \ ___ | | ___  _ __ (_) _____  __ ")
    print(r"       | |_) / _ \| |/ _ \| '_ \| |/ _ \ \/ / ")
    print(r"       |  __/ (_) | | (_) | | | | |  __/>  < ")
    print(r"       |_|   \___/|_|\___/|_| |_|_|\___/_/\_\ ")
    print(r"               _____              _      _           _ ")
    print(r"              |_   _| __ __ _  __| | ___| |__   ___ | |_ ")
    print(r"                | || '__/ _` |/ _` |/ _ \ '_ \ / _ \| __| ")
    print(r"                | || | | (_| | (_| |  __/ |_) | (_) | |_ ")
    print(r"                |_||_|  \__,_|\__,_|\___|_.__/ \___/ \__| ")
    print("                                 Connected to Poloniex.com  ", C.r)


def welcome():
    print("\n\n                  pip install --upgrade ccxt")
    print(C.F.gr, '   please use referral:', C.F.cyn, 'F8GSBSS5', C.r, '            ')


def completed():
    print('             referral code:', C.F.cyn, 'F8GSBSS5', C.r)
    print(C.F.gr, "         ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾")
    print(r"            _    _ _   _____              _ ")
    print(r"           / \  | | | |_   _| __ __ _  __| | ___  ___ ")
    print(r"          / _ \ | | |   | || '__/ _` |/ _` |/ _ \/ __| ")
    print(r"         / ___ \| | |   | || | | (_| | (_| |  __/\__ \ ")
    print(r"        /_/   \_\_|_|   |_||_|  \__,_|\__,_|\___||___/ ")
    print("          ____                      _      _           _ ")
    print("         / ___|___  _ __ ___  _ __ | | ___| |_ ___  __| | ")
    print(r"        | |   / _ \| '_ ` _ \| '_ \| |/ _ \ __/ _ \/ _` | ")
    print("        | |__| (_) | | | | | | |_) | |  __/ ||  __/ (_| | ")
    print(r"         \____\___/|_| |_| |_| .__/|_|\___|\__\___|\__,_| ")
    print("                             |_| ")
    print("         ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾ ")
    exit_tradebot(True)


def exit_tradebot(good_exit=False):
    if good_exit:
        print(C.F.bl, r"   ______  __ __   ____  ____   __  _      __ __   ___   __ __  ")
        print(r"   |      ||  |  | /    ||    \ |  |/ ]    |  |  | /   \ |  |  | ")
        print(r"   |      ||  |  ||  o  ||  _  ||  ' /     |  |  ||     ||  |  | ")
        print(r"   |_|  |_||  _  ||     ||  |  ||    \     |  ~  ||  O  ||  |  | ")
        print(r"     |  |  |  |  ||  _  ||  |  ||     \    |___, ||     ||  :  | ")
        print(r"     |  |  |  |  ||  |  ||  |  ||  .  |    |     ||     ||     | ")
        print(r"     |__|  |__|__||__|__||__|__||__|\_|    |____/  \___/  \__,_| ", C.r)
        print('       please use referral code:', C.F.cyn, 'F8GSBSS5', C.r)
    else:
        print("sorry please try again")
    exit(0 if good_exit else 1)


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


def help_text():
    return """TradeBot — CLI arguments and menu

Arguments:
  -run              Run the bot without menu (best with --budget)
  -log              Extra log output in console
  --budget 0.0001   Per-coin target balance in quote currency
  --sell             Sell-only mode
  --no-sell          Buy-only mode
  --excl COIN ...    Exclude coins from trading (must be last argument)
                     --excl without coins resets the exclude list

Menu options:
  1  Start bot       Update markets, build orders, place orders
  2  Update markets Refresh markets, currencies, balances, tickers
  3  Total balance   Show portfolio value in quote currency; save to config
  4  Build orders    Build order list from order books (no trading)
  5  Order list      Preview built orders
  6  Place orders    Execute BUY/SELL limit orders on Poloniex
  7  Exclude list    Coins to skip (also in config.json)
  8  Budget          Target worth per altcoin market (in quote currency)
  9  Help / extras   Open orders, documentation
  0  Exit

Quote currency (config.json "quote_currency"):
  BTC   — classic BTC pairs (e.g. ADA/BTC); budget 0 sells down
  USDT  — stablecoin pairs (e.g. ADA/USDT); budget 0 sells down
  USDC  — same as USDT with USDC pairs; budget 0 sells down
  After changing quote, run Update Markets to rebuild pair lists.

Tips:
  • Budget is per coin — total buys are capped to ~95% of free quote balance.
  • Use "advice" (80% of balance ÷ market count) as a safe per-coin budget.
  • Whitelist your IP on Poloniex if balance fetch returns 401.
"""


def help_menu():
    print(help_text())
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
        with open_text("config.json", 'w') as load_configfile:  # open file in write mode
            json.dump(new_config_item, load_configfile, indent=4)
        print("            Created the default ₿ 0.0 config.json  ")

    balance_ok = False
    while True:
        try:
            fetch_markets = polo.fetch_markets()
            with open_text("json/poloniex_markets.json", "w") as outfile:
                json.dump(fetch_markets, outfile, sort_keys=True, indent=4)
            if show or args.log:
                print(C.d, "{:>30}".format('poloniex_markets.json'), '    saved', C.r)
            update_progress(10 / 100.0)

            polo_currencies = polo.fetch_currencies()
            with open_text("json/poloniex_currencies.json", "w") as outfile:
                json.dump(polo_currencies, outfile, sort_keys=True, indent=4)
            if show or args.log:
                print(C.d, "{:>30}".format(' poloniex_currencies.json'), '    saved', C.r)
            update_progress(20 / 100.0)

            try:
                polo_fetch = polo.fetch_balance()
                with open_text("json/poloniex_balances_full.json", "w") as outfile:
                    json.dump(polo_fetch, outfile, sort_keys=True, indent=4)
                if show or args.log:
                    print(C.d, "{:>30}".format(' poloniex_balances_full.json'), '    saved', C.r)
                update_progress(30 / 100.0)
                res = balances_dict_from_ccxt(polo_fetch)
                balance_ok = True
            except ccxt.BaseError as exc:
                print(C.F.orng + auth_error_help(exc) + C.r)
                res = {"BTC": ["0"]}
                if os.path.exists("json/poloniex_balances.json"):
                    with open_text("json/poloniex_balances.json", "r") as cached:
                        res = json.load(cached)
                    print("  Using cached poloniex_balances.json until API access works.")
                update_progress(30 / 100.0)

            polo_tickers = polo.fetch_tickers()
            with open_text("json/poloniex_tickers.json", "w") as outfile:
                json.dump(polo_tickers, outfile, sort_keys=True, indent=4)
            if show or args.log:
                print(C.d, "{:>30}".format(' poloniex_tickers.json'), '    saved', C.r)
            update_progress(40 / 100.0)

            with open_text("json/poloniex_balances.json", "w") as outfile:
                json.dump(res, outfile, sort_keys=True, indent=4)
            if show or args.log:
                print(C.d, "{:>30}".format(' poloniex_balances.json'), '    saved', C.r)
            update_progress(70 / 100.0)
            if not balance_ok:
                print(C.F.orng + "  Balance/trading disabled until Poloniex accepts your API key/IP." + C.r)
            break
        except (TimeoutError, ccxt.NetworkError) as exc:
            print("             Network error, please retry:", exc)
            exit(1)
        except ccxt.BaseError as exc:
            print(C.F.rd + "             Poloniex API error:", exc, C.r)
            print(auth_error_help(exc))
            exit(1)

    if show:
        menu()
    return ()


def market_list():  # 2
    with open_text('json/poloniex_markets.json', 'r') as openfile:  # Opening JSON file
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
    with open_text("json/poloniex_live_market.txt", 'w') as outfile:  # open file in write mode
        for market in live_market:
            outfile.write("%s\n" % market)  # write each item on a new line
    if args.log:
        print("           All the live_Markets:", len(live_market))
        print('   All live markets as json/poloniex_live_market.txt  saved')
    update_progress(80 / 100.0)
    with open_text('config.json', 'r') as cfgfile:
        quote_cfg = json.load(cfgfile)
    selected_markets = markets_from_config(quote_cfg)
    for idx, quote in enumerate(selected_markets):
        quote_market_list = filter_live_markets(live_market, quote)
        with open_text(os.path.join("json", markets_filename(quote)), 'w') as outfile:
            for pair in quote_market_list:
                outfile.write("%s\n" % pair)
        if args.log:
            print("           All the %s markets:" % quote, len(quote_market_list))
            print('   All %s markets as json/%s  saved' % (quote, markets_filename(quote)))
        if len(selected_markets) > 1:
            update_progress((80 + (10 * (idx + 1) / len(selected_markets))) / 100.0)
    if len(selected_markets) == 1:
        update_progress(90 / 100.0)
    listed()


def listed():  # 3
    with open_text('json/poloniex_currencies.json', 'r') as openfile:  # Opening JSON file
        json_object = json.load(openfile)  # Reading from json file
    key_list = json_object.keys()
    listed_coins = []
    for x in sorted(key_list):
        if currency_is_tradable(json_object[x]) and is_valid_trading_symbol(x):
            listed_coins.append(x)
    with open_text("json/poloniex_ListedCoins.txt", 'w') as outfile:  # open file in write mode
        for coins in listed_coins:
            outfile.write("%s\n" % coins)  # write each item on a new line
    if args.log:
        print("   Listed tradable coins:", len(listed_coins))
        print('   All listed coins as json/poloniex_ListedCoins.txt  saved')
    update_progress(90 / 100.0)
    make_poloniex_coins()


def make_poloniex_coins():  # 4
    with open_text('config.json', 'r') as cfgfile:
        quote_cfg = json.load(cfgfile)
    selected_markets = markets_from_config(quote_cfg)

    listed_coins = []
    with open_text("json/poloniex_ListedCoins.txt", 'r') as outfile2:
        for line2 in outfile2:
            y = line2[:-1]
            listed_coins.append(y)

    for quote in selected_markets:
        _write_pairs_for_quote(quote, listed_coins, quote_cfg)

    total_balance()


def _write_pairs_for_quote(quote, listed_coins, config):
    quote_markets = []
    with open_text(os.path.join("json", markets_filename(quote)), 'r') as outfile:
        for line in outfile:
            x = line[:-1]
            quote_markets.append(x)

    poloniex_coinlist = []
    counter = 0
    max_index = len(listed_coins) - 1
    while counter <= max_index:
        coin = listed_coins[counter]
        if not is_valid_trading_symbol(coin):
            counter = counter + 1
            continue
        symbol = market_id(coin, quote)
        for x in quote_markets:
            if symbol == x:
                poloniex_coinlist.append(coin)
        counter = counter + 1

    pairs_file = pairs_filename(quote)
    with open_text(os.path.join("json", pairs_file), 'w') as outfile:
        for coin in poloniex_coinlist:
            outfile.write("%s\n" % coin)
        if args.log:
            print("        %s markets:" % quote, len(poloniex_coinlist))
            print('        %s markets as json/%s  saved' % (quote, pairs_file))
    update_progress(100 / 100.0)
    apply_default_market_excludes(poloniex_coinlist, quote, config)


def apply_default_market_excludes(pair_coins, quote, config=None):
    """When many pairs exist and exclude is empty, disable markets with no holdings."""
    global exclude_list
    if len(pair_coins) <= 40:
        return
    if config is None:
        with open_text('config.json', 'r') as cfgfile:
            config = json.load(cfgfile)
    if config.get("exclude"):
        return
    try:
        with open_text('json/poloniex_balances.json', 'r') as handle:
            balances = json.load(handle)
        with open_text('json/poloniex_tickers.json', 'r') as handle:
            tickers = json.load(handle)
    except (OSError, json.JSONDecodeError, KeyError):
        return
    suggested = [
        market_id(coin, quote)
        for coin in suggest_excludes_for_unheld(pair_coins, balances, tickers, quote)
    ]
    active = len(pair_coins) - len(suggested)
    if active <= 0:
        return
    existing = list(config.get("exclude") or [])
    config["exclude"] = sorted(set(existing + suggested))
    exclude_list = config["exclude"]
    with open_text('config.json', 'w') as cfgfile:
        json.dump(config, cfgfile, indent=4)
    if args.log:
        print(
            "  Active %s markets (with holdings): %d / %d" % (quote, active, len(pair_coins))
        )
        print(
            "  %d %s markets excluded (no balance) — change selection in Markets panel"
            % (len(suggested), quote)
        )


def get_open_orders(show=False):
    print("             Open orders on Poloniex")
    try:
        orders = polo.fetch_open_orders()
    except ccxt.BaseError as exc:
        print(C.F.rd, "  failed to fetch open orders:", exc, C.r)
        print(auth_error_help(exc))
        if show:
            menu()
        return []
    if not orders:
        print("          No open orders found.")
    else:
        print("          %d open order(s):" % len(orders))
        print("{:>14} {:>6} {:>16} {:>16} {:>12}".format(
            "Symbol", "Side", "Amount", "Price", "Id"))
        for order in orders:
            print("{:>14} {:>6} {:>16.8f} {:>16.8f} {:>12}".format(
                order.get("symbol", "?"),
                str(order.get("side", "?")).upper(),
                float(order.get("amount") or 0),
                float(order.get("price") or 0),
                str(order.get("id", "?")),
            ))
    if show:
        menu()
    return orders


def total_balance(show=False):
    with open_text('config.json', 'r') as cfgfile:
        balance_cfg = json.load(cfgfile)
    selected_markets = markets_from_config(balance_cfg)
    with open_text('json/poloniex_balances.json', 'r') as openBalances:
        balances = json.load(openBalances)
    with open_text('json/poloniex_tickers.json', 'r') as openTickers:
        tickers = json.load(openTickers)

    market_balances = {}
    for quote in selected_markets:
        coins = load_pair_coins(None, quote)
        wallet = portfolio_in_quote(balances, tickers, coins, quote)
        market_balances[quote] = wallet
        quote_free = float((balances.get(quote) or ["0"])[0])
        if show or args.log:
            print("{:>20}".format(quote), "  ====>", "{:>14}".format(format_quote_value(quote, quote_free)))
        for x in coins:
            if x in balances and x != quote:
                pair = ccxt_symbol(x, quote)
                if pair not in tickers:
                    continue
                last_price = float(tickers[pair]['last'])
                amount = balances.get(x)[0]
                alt_total = float(last_price) * float(amount)
                if show or args.log:
                    print(f"{x:>20}", "  ====>", "{:>14}".format(format_quote_value(quote, alt_total)))
        if show or args.log:
            print("        total %s available:   %s" % (quote, format_quote_value(quote, wallet)))

    primary = primary_quote_from_config(balance_cfg)
    primary_total = market_balances.get(primary, 0.0)
    balance_cfg["markets"] = selected_markets
    balance_cfg["market_balances"] = {
        q: ("%.8f" % v if q == "BTC" else "%.2f" % v)
        for q, v in market_balances.items()
    }
    balance_cfg["balance"] = balance_cfg["market_balances"].get(
        primary, "%.8f" % primary_total if primary == "BTC" else "%.2f" % primary_total
    )
    balance_cfg["quote_currency"] = primary
    with open_text('config.json', 'w') as jsonfile:
        json.dump(balance_cfg, jsonfile, indent=4)
    if show:
        menu()


def advice(show=False):
    with open_text('config.json', 'r') as configfile:
        load_advice_config = json.load(configfile)
    selected_markets = markets_from_config(load_advice_config)
    mybudget = float(load_advice_config["budget"])
    total_active = 0
    total_pairs = 0
    advice_values = {}

    for quote in selected_markets:
        all_coins = load_pair_coins(None, quote)
        active_coins = active_pair_coins(None, quote, config=load_advice_config)
        total_active += len(active_coins)
        total_pairs += len(all_coins)
        quote_balance = market_balance_from_config(load_advice_config, quote)
        market_count = max(len(active_coins), 1)
        input_advice = round((quote_balance * 0.8) / market_count, 6)
        if quote != "BTC":
            input_advice = round(input_advice, 2)
        advice_values[quote] = input_advice

    primary = primary_quote_from_config(load_advice_config)
    input_advice = advice_values.get(primary, 0.0)

    if show or args.log:
        if len(selected_markets) == 1:
            quote = selected_markets[0]
            active_coins = active_pair_coins(None, quote, config=load_advice_config)
            all_coins = load_pair_coins(None, quote)
            market_count = max(len(active_coins), 1)
            if len(active_coins) == len(all_coins):
                print("         ", market_count, "%s markets" % quote)
            else:
                print(
                    "         ", len(active_coins), "active /", len(all_coins),
                    "%s markets" % quote,
                )
            quote_balance = market_balance_from_config(load_advice_config, quote)
            print("               %s available  :  %s" % (quote, format_quote_value(quote, quote_balance)))
        else:
            print("         ", total_active, "active /", total_pairs, "markets (BTC + USDT)")
            for quote in selected_markets:
                quote_balance = market_balance_from_config(load_advice_config, quote)
                print("               %s available  :  %s" % (quote, format_quote_value(quote, quote_balance)))
        adv = str("%.6f" % input_advice) if primary == "BTC" else str("%.2f" % input_advice)
        label = "advice 80%% of %s" % primary
        if mybudget < input_advice:
            print("           ", label, ":", C.F.gr,
                  format_quote_value(primary, input_advice)[:8], C.r)
        else:
            print("           ", label, ":  ", C.F.rd + adv, C.r)

    load_advice_config["advice"] = input_advice
    load_advice_config["advice_by_market"] = advice_values
    load_advice_config["markets"] = selected_markets
    load_advice_config["quote_currency"] = primary
    with open_text('config.json', 'w') as jsonfile:
        json.dump(load_advice_config, jsonfile, indent=4)
    return {
        "markets": total_active,
        "markets_total": total_pairs,
        "balance": market_balance_from_config(load_advice_config, primary),
        "advice": input_advice,
        "budget": mybudget,
        "quote_currency": primary,
        "selected_markets": selected_markets,
    }


def collect_orders(show=False):
    global item, orderPrint, price
    market = 'LIMIT'  # LIMIT_MAKER - MARKET
    with open_text('config.json', 'r') as configfile:
        load_config_coinlist = json.load(configfile)
    selected_markets = markets_from_config(load_config_coinlist)
    trade_pairs = []
    for quote in selected_markets:
        for alt_coin in active_pair_coins(None, quote, config=load_config_coinlist):
            trade_pairs.append((alt_coin, quote))
    if not trade_pairs:
        print("  No active markets — enable coins in the Markets panel or clear the exclude list.")
        with open_text("json/orderlist.json", "w") as orderlistFile:
            json.dump([], orderlistFile, indent=4)
        if show:
            menu()
        return
    with open_text('json/poloniex_balances.json', 'r') as openBalances:
        balances = json.load(openBalances)
    with open_text('json/poloniex_tickers.json', 'r') as openTickers:
        tickers = json.load(openTickers)
    buy_budget_by_quote = {
        quote: max(0.0, load_quote_available("json/poloniex_balances.json", quote) * 0.95)
        for quote in selected_markets
    }
    counter = 0
    max_index = len(trade_pairs) - 1
    progress = ProgressBar(len(trade_pairs), fmt=ProgressBar.FULL)
    coin_total = max(len(trade_pairs), 1)
    orders_list = []
    while counter <= max_index:  # while = loop through trade pairs until max_index
        abort_if_cancelled()
        progress()
        progress.current += 1
        update_progress(progress.current / float(coin_total))
        alt_coin, quote = trade_pairs[counter]
        min_order = min_order_for_quote(quote)
        remaining_buy_budget = buy_budget_by_quote.get(quote, 0.0)
        if not is_valid_trading_symbol(alt_coin):
            counter = counter + 1
            continue
        symbol = ccxt_symbol(alt_coin, quote)
        pair = market_id(alt_coin, quote)
        if alt_coin in balances:
            jv1 = balances.get(alt_coin)[0]
            alt_total = float(jv1)  # Get your amount of the altcoin
        else:
            alt_total = float(0.0)
        if symbol not in tickers:
            counter = counter + 1
            continue
        budget_input = coin_budget_from_config(load_config_coinlist, market_id(alt_coin, quote))
        last_price = float((tickers[symbol]['last']))
        alt_worth = float(last_price) * float(alt_total)
        headline = str("  %s" % format_quote_value(quote, last_price))
        try:
            fetch_orderbook = polo.fetch_order_book(symbol, 5)
        except (ccxt.ExchangeError, ccxt.NetworkError):
            counter = counter + 1
            continue
        with open_text("orderbooks/" + pair + ".json", "w") as outfile:
            json.dump(fetch_orderbook, outfile, indent=4)
        with open_text("orderbooks/" + pair + ".json", 'r') as openfile:
            orderbook = json.load(openfile)  # Reading from json file
        asks = orderbook['asks']  # [[Price, Amount],[...]]
        if not asks or not orderbook.get('bids'):
            counter = counter + 1
            continue
        ask = asks[0][0]  # Collect latest Sell(ask) prices
        bids = orderbook['bids']  # [[Amount, Price],[...]]
        bid = bids[0][0]  # Collect latest Buy (bid) prices
        if args.log:
            print("         latest prices Sell(ask)", ask, "Buy(bid)", bid)
        while True:  # Check if the alt_worth is Higher or Lower than Budget (script-input)
            try:
                buy_only = args.sell is False and getattr(args, "buy", None) is not False
                sell_only = args.sell is True
                if float(alt_worth) >= float(budget_input):  # Higher = SELL
                    if buy_only or is_pair_excluded(alt_coin, quote, exclude_list):
                        side = "exclude"
                    else:
                        side = "SELL"
                    order_worth = float(alt_worth) - float(budget_input)  # Calculate how much to sell in BTC
                    alt_amount = float(order_worth) / float(bid)  # Calculate how much AltCoins to Sell
                    price_list = bids
                    break  # stop if loop
                else:
                    if sell_only or is_pair_excluded(alt_coin, quote, exclude_list):
                        side = "exclude"
                    else:
                        side = "BUY"
                    order_worth = float(budget_input) - float(alt_worth)  # Calculate how much to buy in BTC
                    order_worth = min(order_worth, remaining_buy_budget)
                    if order_worth < min_order:
                        side = "exclude"
                        price_list = asks
                        break
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
                if min_order > order_worth:
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
                    print("               " + "{:<7}".format(alt_coin) + " are Worth: %s" % format_quote_value(quote, alt_worth))

                if side == "exclude" or is_pair_excluded(alt_coin, quote, exclude_list):
                    print(C.F.cyn, "  ", "{:<7}".format(alt_coin), "Exclude", C.r)
                elif min_order < order_worth:
                    if is_test_mode():
                        print(C.F.yel, "  ", "{:<7}".format(alt_coin), " TEST = %s" % format_quote_value(quote, order_worth), C.r)
                    elif side == "BUY":
                        print(C.F.rd, "  ", "{:<7}".format(alt_coin), " Buy = %s" % format_quote_value(quote, order_worth), C.r)
                    else:
                        print(C.F.gr, "  ", "{:<7}".format(alt_coin), "Sell = %s" % format_quote_value(quote, order_worth), C.r)
                break
            except IndexError:
                print(" Orderbook smaller than 5")
                break
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
                        if side == "BUY":
                            buy_budget_by_quote[quote] = max(
                                0.0,
                                buy_budget_by_quote.get(quote, 0.0) - float(order_worth),
                            )
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
        gui_sleep(0.001)
        counter = counter + 1
    progress.done()
    with open_text("json/orderlist.json", "w") as orderlistFile:
        json.dump(orders_list, orderlistFile, indent=4)
    print('             json/orderlist.json                        saved')
    with open_text("json/prev_order.json", "a") as prevOrderFile:
        json.dump(orders_list, prevOrderFile, indent=4)
    if orders_list:
        print("  %d order(s) ready — run Preview or Place Orders" % len(orders_list))
    else:
        print("  No orders built — each coin was below the minimum order size.")
        print("  Increase per-coin budget or holdings, then run Build Orders again.")
    if show:
        menu()


def order_list(place=False):
    while True:
        try:
            global status, trade_amount, symbol, side, amount, quantity, price, total, alt, side_color
            dry_test = bool(place) and is_test_mode()
            do_place = bool(place) and not dry_test
            with open_text('json/orderlist.json', 'r') as open_orderlist:  # Opening JSON file
                orders = json.load(open_orderlist)  # Reading from json file
            if not orders:
                print("  Order list is empty — run Build Orders after increasing budget or holdings.")
                if not _interactive_menu:
                    break
                menu()
                continue
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
            print("{:>12}".format("| Order"), "{:>22}".format("|    Amount of altcoin "), "{:>12}".format(" |    Price   "),
                  "{:>18}".format(" |     Total     |"), " status  |")
            incomplete = []
            cost_total = 0.0
            with open_text('config.json', 'r') as cfgfile:
                order_cfg = json.load(cfgfile)
            order_quote = quote_from_config(order_cfg)
            remaining_quote = load_quote_available("json/poloniex_balances.json", order_quote) if do_place else 0.0
            order_total = max(max_index + 1, 1)
            preview_test = (not do_place) and is_test_mode()
            if do_place and remaining_quote > 0:
                print(C.F.gr, "          %s free for buys: %s" % (
                    order_quote, format_quote_value(order_quote, remaining_quote)), C.r)
            while nr <= max_index:  # while = loop through PoloniexCoins List until max_index
                abort_if_cancelled()
                update_progress((nr + 1) / float(order_total))
                symbol = orders[nr]['symbol']
                tradetype = orders[nr]['type']
                side = orders[nr]['side']
                amount = orders[nr]['alt_amount']
                quantity = orders[nr]['quantity']
                price = orders[nr]['price']
                total = orders[nr]['total']
                alt = orders[nr]['alt']
                if do_place:
                    if lagg < 360:
                        try:
                            if side == "exclude" or alt in exclude_list:
                                side_color = C.F.cyn
                                status = "  " + C.F.cyn + "exclude" + C.r + "   "
                                trade_amount = "{:>16}".format("     ---      ")
                            elif side == "BUY":
                                order_cost = float(total)
                                if order_cost > remaining_quote:
                                    side_color = C.F.orng
                                    status = "  " + C.F.orng + "low %s" % order_quote + C.r + "   "
                                    trade_amount = "{:>16}".format("     ---      ")
                                    incomplete.append(orders[nr])
                                    if args.log:
                                        print(C.F.orng,
                                              "  skip BUY", alt,
                                              "need %s have %s" % (
                                                  format_quote_value(order_quote, order_cost),
                                                  format_quote_value(order_quote, remaining_quote)),
                                              C.r)
                                else:
                                    polo.create_order(
                                        symbol,
                                        order_type_for_ccxt(tradetype),
                                        order_side_for_ccxt(side),
                                        amount,
                                        price,
                                    )
                                    remaining_quote -= order_cost
                                    side_color = C.F.rd
                                    status = "  " + C.F.rd + "Complete" + C.r + "   "
                                    trade_amount = "{:>16}".format("%.8f" % amount)
                                    gui_sleep(0.5)
                            elif side == "SELL":
                                polo.create_order(
                                    symbol,
                                    order_type_for_ccxt(tradetype),
                                    order_side_for_ccxt(side),
                                    amount,
                                    price,
                                )
                                side_color = C.F.gr
                                status = "  " + C.F.gr + "Complete" + C.r + "   "
                                trade_amount = "{:>16}".format("%.8f" % quantity)
                                gui_sleep(0.5)
                        except ccxt.ExchangeError as exc:
                            status = "INCOMPLETE"
                            side_color = C.F.prpl
                            incomplete.append(orders[nr])
                            trade_amount = C.r + "{:>16}".format("%.8f" % amount)
                            if is_insufficient_balance_error(exc):
                                remaining_quote = 0.0
                            print(C.F.rd, "  order failed:", exc, C.r)
                        except ccxt.NetworkError as exc:
                            status = "INCOMPLETE"
                            side_color = C.F.prpl
                            incomplete.append(orders[nr])
                            trade_amount = C.r + "{:>16}".format("%.8f" % amount)
                            if args.log:
                                print(C.F.rd, "  network error:", exc, C.r)
                elif side == "exclude" or alt in exclude_list:
                    side_color = C.F.cyn
                    status = C.r + "  " + C.F.cyn + "exclude" + C.r + "   "
                    trade_amount = "{:>16}".format("      ---      ")
                else:
                    if preview_test or dry_test:
                        side_color = C.F.yel
                        status = "{:>9}".format("Test")
                    elif side == "BUY":
                        side_color = C.F.rd
                        status = "{:>9}".format("Preview")
                    elif side == "SELL":
                        side_color = C.F.gr
                        status = "{:>9}".format("Preview")
                    else:
                        side_color = C.F.yel
                        status = "{:>9}".format("Preview")
                    trade_amount = "{:>16}".format("%.8f" % amount)
                if side not in ("exclude",) and alt not in exclude_list:
                    try:
                        cost_total += float(total)
                    except (TypeError, ValueError):
                        pass
                tot = "  %.8f" % total
                tot_st = tot[:8].replace("0", "*")
                side_label = "TEST" if (dry_test or preview_test) and side in ("BUY", "SELL") else side
                tot_display = (tot_st + tot[8:]).replace("*.", "₿ 0.")
                print(side_color,
                      "{:>12}".format(f"{side_label:>10}"), C.r,
                      "{:>22}".format(trade_amount+f" {alt:<7}"),
                      "{:>12}".format("%.8f" % float(price)),
                      side_color, "{:>15}".format(tot_display), C.r,
                      side_color, status, C.r)
                gui_sleep(0.1)
                nr = nr + 1

            if dry_test or preview_test:
                print(C.F.yel,
                      "  Total cost (test):", format_quote_value(order_quote, cost_total),
                      C.r)
            else:
                print("  Total cost:", format_quote_value(order_quote, cost_total))

            if dry_test:
                print(C.F.yel, "  TEST completed", C.r)
                menu()
            elif do_place:
                if incomplete:
                    with open_text("json/orderlist_incomplete.json", "w") as orderlist_incomplete:
                        json.dump(incomplete, orderlist_incomplete, indent=4)
                    print(C.F.orng,
                          "  %d order(s) failed or skipped — see json/orderlist_incomplete.json" % len(incomplete),
                          C.r)
                    menu()
                else:
                    completed()
            else:
                menu()
            if not _interactive_menu:
                break
        except ConnectionError:
            menu()
            if not _interactive_menu:
                break


def start_bot():
    get_update()
    market_list()
    collect_orders()
    order_list(True)


def menu():
    with open_text('config.json', 'r') as menu_configfile:
        load_menu_config = json.load(menu_configfile)
    print("\n ")
    print('            |‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾|')
    print("            |     1: start bot " + C.F.gr + " ₿ %.5f" % float(load_menu_config["budget"]) + C.r + "      |")
    print('            |     2: update markets            |')
    print('            |     3: total_balance             |')
    print('            |     4: build orders              |')
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

    parse_cli_args()
    welcome()
    logo()
    get_update()
    market_list()
    get_inputs()
    with open_text('config.json', 'r') as configfile:
        loadconfig = json.load(configfile)
    budget = float(loadconfig["budget"])
    exclude_list = loadconfig["exclude"]
    if args.run:
        set_interactive_menu(False)
        start_bot()
        sys.exit(0)
    menu()
