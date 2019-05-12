#!/usr/bin/env python3
# Before running this script you need to
# 1) Install Python 3 (select add to PATH)
# 2) Type in CMD: python -m pip install --upgrade pip
# 3) Type in CMD: pip3 install https://github.com/s4w3d0ff/python-poloniex/archive/v0.4.7.zip
# 4) Adjust in this script on line 29: 'Your_Poloniex_Key_Here' & 'Your_Poloniex_Secret_Here'
# 5) In CMD Navigate to PoloniexTradeBot folder
# 6) Run the script: python AllCoinsInBTC.py 0.001 
# Where 0.001 is the BTC Value for each Altcoin 
# Script by BitcoinDaytraderChannel@gmail.com
# Youtube.com/c/BitcoinDaytrader
    
# Import Standard Library Modules
import time
import sys
# Import the External Poloniex Library (python-poloniex-master folder + PIP install poloniex)
import poloniex 
from poloniex import Poloniex

try: # First check for user BTC Value input
	budget = str(sys.argv[1])#.format('0.001')
except: # Print an Exeption (error) if there is no input
	print("put Budget in as python AllCoinsInBTC.py 0.001")
	exit(1)

while True: # Setup to connect to Poloniex API
	try:
		polo = Poloniex()
		polo.key = 'Your_Poloniex_Key_Here'
		polo.secret = 'Your_Poloniex_Secret_Here'
		print(" ")
		print("---!Connected to Poloniex.com!---")
		break
	except:
		backoff("Can not connect to Poloniex API")
		exit(1)
		
def backoff(msg): # Function for the Error Message later in script
    print(msg)
    time.sleep(0.1)

def decor (func):
	def wrap():
		print(" #################")
		func()
		print(" #################")
	return wrap

@decor #send print_budget to decor function 
def print_budget():
	print(" # Budget=", budget , "#") # Show budget input
@decor
def print_pair():
	print("# Market =", pair , "#") # Show name of Market
			
if __name__ == '__main__':	# Start the main BUY/SELL script
	print_budget();
	PoloniexCoins = ["ARDR","ATOM","BAT","BCHABC","BCHSV","BCN","BNT","BTS","CLAM","CVC","DASH","DCR","DGB","DOGE","EOS","ETC","ETH","FCT","FOAM","GAME","GAS","GNT","GRIN","KNC","LBC","LOOM","LPT","LSK","LTC","MANA","MAID","NAV","NMR","NXT","OMG","OMNI","PASC","POLY","QTUM","REP","SC","SNT","STEEM","STORJ","STR","STRAT","VIA","VTC","XEM","XMR","XPM","XRP","ZEC","ZRX"]
	counter = 0 # Where to start in list (0=AMP, 1=ARDR, 2=BAT...)
	max_index = len(PoloniexCoins) - 1 # Length PoloniexCoins List - 1  List start at 0 not 1 
	print("Total amount of Altcoins on Poloniex BTC Market = " , max_index)
	while counter <= max_index: # while = loop through PoloniexCoins List until max_index
		AltCoin = PoloniexCoins[counter] # Every loop change variable AltCoin to counter (0=AMP, 1=ARDR, 2=BAT...)
		pair = "BTC_" + AltCoin # Market: BTC_ + AltCoin to create coinpairs (BTC_AMP , BTC_ARDR, BTC_BAT...)
		print_pair();

		while True: #0 First check if the coinpair already has a Open Order & Cancel it
			try:
				returnOpenOrders = polo.returnOpenOrders()[pair] # Collect the open orders of the coinpair			
				if returnOpenOrders != []: # if the openorders are not empty Cancel the Order
					returnOrderNumber = polo.returnOpenOrders()[pair][0]['orderNumber'] # Collect last orderNumber	
					returnOrderAmount = polo.returnOpenOrders()[pair][0]['amount'] # Collect OrderAmount
					print("Open Order: ", returnOrderNumber, "Total Amount in BTC: " , returnOrderAmount ) # OpenOrder Info
					cancelOrder = polo.cancelOrder(returnOrderNumber)# cancel order with latest orderNumber
					print("---!CANCEL Complete!---") # Reloop the OpenOrder Check						
				else: # if the openorders are not empty
					#print("---!No OpenOrders!---")
					break				
			except: # Print an Exeption (error) if script can't collect Orders
				backoff("Can not get the OpenOrder")
				exit(1) # Exit the entire script
		
		while True: #1 get the ticker of the coinpair (LowestAsk & HighestBid Price)
			try:
				Ask = polo.returnTicker()[pair]['lowestAsk'] # Collect latest Sell(ask) & Buy (bid) prices
				Bid = polo.returnTicker()[pair]['highestBid']
				#print("Sell price in BTC = " , Ask)
				#print("Buy  price in BTC = " , Bid)
				break
			except:
				backoff("Can not get the Ask and Bid Price")
				exit(1)

		while True: #2 Get the total amount of altcoins
			try:
				AltTotal = polo.returnBalances()[AltCoin] # Get the amount of the altcoin
				#print("I have total ", AltCoin ,"= " , AltTotal)
				break
			except:
				backoff("Can not get the total amount of coins")
				exit(1)
		
		while True: #3 calculate the total Alt Worth in BTC
			try:
				AltWorth = float(Bid) * float(AltTotal) # Float for numbers with decimals (Bid see #1) (AltTotal see #2)
				#print("My" , AltCoin , "worth in BTC = " , AltWorth)
				break
			except:
				backoff("Can not calculate altcoin total worth")
				exit(1)
		
		while True: #4 Check if the AltWorth(see #3) is Higher or Lower than Budget (script-input)	
			try:
				if float(AltWorth) >= float(budget): #Higher = SELL 
					#print("AltWorth is higher then budget")
					AltSellWorth = float(AltWorth) - float(budget) # Calculate how much to sell in BTC
					print("AltSellWorth in btc = " , AltSellWorth)
					AltSell = float(AltSellWorth) / float(Bid) # Calculate how much AltCoins to Sell
					AltBuyWorth = 100 # To fix error when not defined in => #5 Orderbook
					break # stop if loop
				else: #------------------------------#Lower  = BUY 
					#print("AltWorth is lower then budget")
					AltBuyWorth = float(budget) - float(AltWorth) # Calculate how much to buy in BTC
					print("AltBuyWorth in btc = " , AltBuyWorth)
					AltBuy = float(AltBuyWorth) / float(Ask) # Calculate how much AltCoins to Buy
					AltSellWorth = 100 # To fix error when not defined in => #5 Orderbook
					break # stop else loop					
			except:
				backoff("The Order does not work, Maybe to small") # Error if can't calculate
				exit(1)
		
		while True: #5 get the orderbook of the coinpair (All Sell & Buy Orders)
			try:
				MinOrder = 0.0001 # Minimal order worth in BTC = Poloniex Trading Rule
				if MinOrder > AltSellWorth: # Compare MinOrder with AltSellWorth (see #4 if)
					print(" ---SELL Order To Small To Place---")
					break # stop if loop
				elif MinOrder > AltBuyWorth: # Compare MinOrder with AltBuyWorth (see #4 else)
					print(" ---BUY Order To Small To Place---")
					break # stop elseif loop	 			
				else: # run the buy/sell part if order is not to small							
					if float(AltWorth) >= float(budget): # SELL!!! Compare SellOrder with Available Bids
						#print("**SELL** AltWorth HIGHER budget")						
						OrderBidsPrice0  = polo.returnOrderBook()[pair]['bids'][0][0] # Collect highest buyorder (0) price
						OrderBidsAmount0 = polo.returnOrderBook()[pair]['bids'][0][1] # Collect highest buyorder (0) amount
						OrderBidsSum0 = float(OrderBidsAmount0) * float(OrderBidsPrice0) # Calculate highest buyorder BTC Value
						
						if float(AltSellWorth) <= float(OrderBidsSum0): # Sell if highest bid (in BTC) is bigger than AltSellWorth (in BTC)
							sell = polo.sell(pair, Bid, AltSell) # Make the SellOrder
							print("---!SELL Complete!--- fitted in first Bid")
							break
						else: # Highest BuyOrder (0) is to small, Calculate for 1st & 2nd BuyOrder (0&1)
							print("Order is Bigger than BidsSum0")
							OrderBidsPrice1  = polo.returnOrderBook()[pair]['bids'][1][0] # Collect 2nd highest buyorder (1) price
							OrderBidsAmount1 = polo.returnOrderBook()[pair]['bids'][1][1] # Collect 2nd highest buyorder (1) amount
							OrderBidsSum1 = float(OrderBidsAmount1) * float(OrderBidsPrice1) # Calculate 2nd highest buyorder BTC Value
							OrderBidsSum01 = float(OrderBidsSum0) + float(OrderBidsSum1) # Calculate 1st & 2nd highest buyorders BTC Value
							
							if float(AltSellWorth) >= float(OrderBidsSum01): #Highest BuyOrders (0&1) to small. Calculate for Order 0,1&2
								print("Order is Bigger than BidsSum01")
								OrderBidsPrice2  = polo.returnOrderBook()[pair]['bids'][2][0] # Collect 3nd highest buyorder (2) price
								OrderBidsAmount2 = polo.returnOrderBook()[pair]['bids'][2][1] # Collect 3nd highest buyorder (2) price
								OrderBidsSum2 = float(OrderBidsAmount2) * float(OrderBidsPrice2) # Calculate 3rd highest buyorder BTC Value
								OrderBidsSum012 = float(OrderBidsSum01) + float(OrderBidsSum2) # Calculate 1st 2nd & 3rd highest buyorders BTC Value
								
								if float(AltSellWorth) >= float(OrderBidsSum012): #Highest BuyOrders (0,1&2) to small. Sell to BuyOrder 0,1,2&3
									print("Order is Bigger than BidsSum012")
									OrderBidsPrice3  = polo.returnOrderBook()[pair]['bids'][3][0] # Collect 4th highest buyorder (3) price
									OrderBidsAmount3 = polo.returnOrderBook()[pair]['bids'][3][1] # Collect 4th highest buyorder (3) amount
									OrderBidsSum3 = float(OrderBidsAmount3) * float(OrderBidsPrice3) # Calculate 4th highest buyorder BTC Value
									OrderBidsSum0123 = float(OrderBidsSum012) + float(OrderBidsSum3) # Calculate 1st 2nd 3rd & 4th highest buyorders BTC Value
									# Sell to the highest 4 bids (buyorders 0,1,2&3)
									sell = polo.sell(pair, OrderBidsPrice3, AltSell)  # Make the SellOrder									
									print("---!SELL Complete!--- fitted in Fourth Bid")										
									break							
								else: # Sell to the highest 3 bids (BuyOrders 0,1&2)
									sell = polo.sell(pair, OrderBidsPrice2, AltSell) # Make the SellOrder
									print("---!SELL Complete!--- fitted in Third Bid")										
									break
									
							else: # Sell to the highest 2 bids (BuyOrders 0&1)						
								sell = polo.sell(pair, OrderBidsPrice1, AltSell) # Make the SellOrder
								print("---!SELL Complete!--- fitted in Second Bid")										
								break																																			
						break # End SELL part (if float(AltWorth) >= float(budget):)				
					else: # BUY!!! Compare BuyOrder with Available Asks (same Logic as SELL part where sell=buy & bid=ask)
						#print("**BUY** AltWorth LOWER budget")
						OrderAsksPrice0  = polo.returnOrderBook()[pair]['asks'][0][0]
						OrderAsksAmount0 = polo.returnOrderBook()[pair]['asks'][0][1]
						OrderAsksSum0 = float(OrderAsksAmount0) * float(OrderAsksPrice0)
						
						if float(AltBuyWorth) <= float(OrderAsksSum0): #Order the OrderBook0 							
							buy = polo.buy(pair, Ask, AltBuy)
							print("---!Buy Complete!--- fitted in first Ask")
							break
						else: #OrderBook0 to small Calculate for Order 0&1
							print("Order is Bigger than AsksSum0")
							OrderAsksPrice1  = polo.returnOrderBook()[pair]['asks'][1][0]
							OrderAsksAmount1 = polo.returnOrderBook()[pair]['asks'][1][1]
							OrderAsksSum1 = float(OrderAsksAmount1) * float(OrderAsksPrice1)
							OrderAsksSum01 = float(OrderAsksSum0) + float(OrderAsksSum1)
							
							if float(AltBuyWorth) >= float(OrderAsksSum01): #Orderbook 0&1 to small. Order 0,1&2
								print("Order is Bigger than AsksSum01")
								OrderAsksPrice2  = polo.returnOrderBook()[pair]['asks'][2][0]
								OrderAsksAmount2 = polo.returnOrderBook()[pair]['asks'][2][1]
								OrderAsksSum2 = float(OrderAsksAmount2) * float(OrderAsksPrice2)
								OrderAsksSum012 = float(OrderAsksSum01) + float(OrderAsksSum2)
								
								if float(AltBuyWorth) >= float(OrderAsksSum012): #Orderbook 01&2 to small. Order 0,1,2&3
									print("Order is Bigger than AsksSum012")
									OrderAsksPrice3  = polo.returnOrderBook()[pair]['asks'][3][0]
									OrderAsksAmount3 = polo.returnOrderBook()[pair]['asks'][3][1]
									OrderAsksSum3 = float(OrderAsksAmount3) * float(OrderAsksPrice3)
									OrderAsksSum0123 = float(OrderAsksSum012) + float(OrderAsksSum3)
									buy = polo.buy(pair, OrderAsksPrice3, AltBuy)
									print("---!BUY Complete!--- fitted in Fourth Bid")										
									break								
								else: #Order the Orderbook 01&2
									buy = polo.buy(pair, OrderAsksPrice2, AltBuy)
									print("---!BUY Complete!--- fitted in Third Bid")										
									break
									
							else: #Order the Orderbook 0&1
								buy = polo.buy(pair, OrderAsksPrice1, AltBuy)
								print("---!BUY Complete!--- fitted in Second Bid")										
								break																			
							break
						break # end BUY part						
				break # end of try
			except:
				backoff("Can not finish the OrderBook")
				exit(1)			
		
		print(" ")
		counter = counter + 1
