# PoloniexTradeBot
Script to automatically buy/sell altcoins to a certain BTC Value

![python](https://img.shields.io/badge/python-2.7%20%26%203-blue.svg)

Download/Clone the entire PoloniexTradeBot folder to your computer

 Before running this TradeBot script you need to make sure the COINLIST (ln 58) is up to date.
```
1) Install Python 3 (select add to PATH)
2) Type in CMD: python -m pip install --upgrade pip
3) Type in CMD: pip3 install https://github.com/s4w3d0ff/python-poloniex/archive/v0.4.7.zip
4) Adjust in the script AllCoinsInBTC.py on line 29: 'Your_Poloniex_Key_Here' & 'Your_Poloniex_Secret_Here'
5) In CMD Navigate to PoloniexTradeBot folder
6) Run the script: python AllCoinsInBTC.py 0.001 
```
Where 0.001 is the BTC Value for each Altcoin 



#### Basic Setup (no api Key/Secret):
```python
from poloniex import Poloniex
polo = Poloniex()

print(polo.returnTicker()['BTC_ETH'])
```

#### Basic Private Setup (Api key/secret required):
```python
import poloniex
polo.key = 'your-Api-Key-Here-xxxx'
polo.secret = 'yourSecretKeyHere123456789'

balance = polo.returnBalances()
print("I have %s ETH!" % balance['ETH'])
```

#### Possible Commands
```python
PUBLIC_COMMANDS = [
    'returnTicker',
    'return24hVolume',
    'returnOrderBook',
    'marketTradeHist',
    'returnChartData',
    'returnCurrencies',
    'returnLoanOrders']

PRIVATE_COMMANDS = [
    'returnBalances',
    'returnCompleteBalances',
    'returnDepositAddresses',
    'generateNewAddress',
    'returnDepositsWithdrawals',
    'returnOpenOrders',
    'returnTradeHistory',
    'returnAvailableAccountBalances',
    'returnTradableBalances',
    'returnOpenLoanOffers',
    'returnOrderTrades',
    'returnActiveLoans',
    'returnLendingHistory',
    'createLoanOffer',
    'cancelLoanOffer',
    'toggleAutoRenew',
    'buy',
    'sell',
    'cancelOrder',
    'moveOrder',
    'withdraw',
    'returnFeeInfo',
    'transferBalance',
    'returnMarginAccountSummary',
    'marginBuy',
    'marginSell',
    'getMarginPosition',
    'closeMarginPosition']
```
