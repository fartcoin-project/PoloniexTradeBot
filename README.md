# PoloniexTradeBot
Script to automatically buy/sell altcoins to a certain BTC Value

![python](https://img.shields.io/badge/python-3-blue.svg)

## Install Guide PoloniexTradebot.py
```
# 1| Install Python 3.11+ from https://www.python.org/ (select add to PATH)
# 2| Install git https://gitforwindows.org/ 
# 3| Open CMD/git-bash/terminal: 
#               pip install ccxt     (CCXT library)
# 4| go to desired directory & clone the repository: 
#               cd  %userprofile%\...
#               git clone https://github.com/fartcoin-project/PoloniexTradeBot.git
#               cd  PoloniexTradeBot-master
# 7) Create tradebot_config.py from tradebot_config.EXAMPLE.py with your Poloniex Key & Secret
# 8) Run the script: python tradebot.py
```

Automatically trade to get the same BTC Value for each Altcoin in BTC market
Script by BitcoinDaytraderChannel@gmail.com
Youtube.com/c/BitcoinDaytrader

### Possible arguments to include 
#### tradebot.py run log --budget 1 --exclude COIN1 COIN2
```
   | -h  --help       =>  help menu                           | 
   |   -run           =>  no input, best with --budget        |
   |   -log           =>  extra log print in console          |
   | --budget         =>  --₿udget 0.0001                     |
   | --sell --no-sell =>  Input the coins to exclude          |
   | --excl [coin ..] =>  Exclude coins from bot              |
   |                        MUST BE LAST ARGUMENT             |
   |                      --excl without coins = reset        |
```
--!!   when signing up for Poloniex   !!--
--!!    Use Referal code F8GSBSS5     !!--
--!! to safe 10% on transaction costs !!--

#### keywords
```
'poloniex', 'btc', 'altcoin', 
'rest', 'poloniexapi', 'exchange', 
'api', 'tradebot'
```

