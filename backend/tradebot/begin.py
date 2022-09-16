# from tradebot import get_open_orders, menu, start_bot, C, print_format_table,
import sys, re
from datetime import datetime

from tradebot import start_bot, menu, get_open_orders


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
