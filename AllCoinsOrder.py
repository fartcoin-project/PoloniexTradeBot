#!/usr/bin/env python3
# Run the script: python AllCoinsOrder.py 0.005 
# Where 0.005 is the BTC Value for each Altcoin 
# Script by BitcoinDaytraderChannel@gmail.com
# Youtube.com/c/BitcoinDaytrader
# Before running this script you need to
# 1) Download the Poloniex Library: https://github.com/s4w3d0ff/python-poloniex/
# 2) pip3 install https://github.com/s4w3d0ff/python-poloniex/archive/v0.4.7.zip
# 3) Place this script in the python-poloniex Folder on your PC
# 4) Adjust on line 35 the Setup: 'Your_Poloniex_Key_Here' & 'Your_Poloniex_Secret_Here'

# Import Standard Library Modules
import time
import sys
# Import the External Poloniex Library (python-poloniex-master folder + PIP install poloniex)
import poloniex 
from poloniex import Poloniex

try: # First check for user BTC Value input
	budget = str(sys.argv[1])#.format('0.005')
	print(" #################")
	print(" # Budget=", budget , "#")	
	print(" #################")
except: # Print an Exeption (error) if there is no input
	print("put Budget in as python AllCoinsOrder.py 0.005")
	exit(1)

def backoff(msg): # Function for the Error Message later in script
    print(msg)
    time.sleep(0.1)
				
while True: # Setup to connect to Poloniex API
	try:
		polo = Poloniex()
		polo.key = 'Your_Poloniex_Key_Here'
		polo.secret = 'Your_Poloniex_Secret_Here'
		break
	except:
		backoff("Can not connect to Poloniex API")
		exit(1)

if __name__ == '__main__':	# Start the main BUY/SELL script
	PoloniexCoins = ["AMP","ARDR","BAT","BCH","BCN","BTS","BURST","CLAM","CVC","DASH","DCR","DGB","DOGE","EOS","ETC","ETH","EXP","FCT","GAME","GAS","GNO","GNT","HUC","KNC","LBC","LOOM","LSK","LTC","MAID","NAV","NMC","NXT","OMG","OMNI","PASC","PPC","REP","SBD","SC","SNT","STEEM","STORJ","STR","STRAT","SYS","VIA","VTC","XCP","XEM","XMR","XPM","XRP","ZEC","ZRX"]
	# Delisted coins: BTCD, BTM, EMC2, GRC, NEOS, POT, VRC, XBC
	counter = 0 # Where to start in list (0=AMP, 1=ARDR, 2=BAT...)
	max_index = len(PoloniexCoins) - 1 # Length of PoloniexCoins List = 62 Minus 1  List start at 0 not 1 
	while counter <= max_index: # while = loop through PoloniexCoins List until max_index
		AltCoin = PoloniexCoins[counter] # Every loop change variable AltCoin to counter (0=AMP, 1=ARDR, 2=BAT...)
		pair = "BTC_" + AltCoin # variable to create coinpairs (BTC_AMP , BTC_ARDR, BTC_BAT...)
		print(" ######################")
		print("# MarketName =", pair , "#") # Show name of Market
		print(" ######################")		

		while True: #0 First check if the coinpair already has a Open Order & Cancel it
			try:
				returnOpenOrders = polo.returnOpenOrders()[pair] # Collect the open orders of the coinpair			
				if returnOpenOrders != []: # if the openorders are not empty
					# Input to Cancel OpenOrder
					returnOrderNumber = polo.returnOpenOrders()[pair][0]['orderNumber'] # Collect last orderNumber	
					returnOrderAmount = polo.returnOpenOrders()[pair][0]['amount'] # Collect OrderAmount
					print("Open Order: ", returnOrderNumber, "Total Amount in BTC: " , returnOrderAmount ) # OpenOrder Info
					print("Do you want to Cancel the Orders?")
					print("y or n")
					user_input = input(": ") # Wait for User Imput to Cancel Order
					if user_input == "n": # no to continue the script
						break
					elif user_input == "y":# yes to cancel
						cancelOrder = polo.cancelOrder(returnOrderNumber)# cancel order with latest orderNumber
						print("---!CANCEL Complete!---") # Reloop the OpenOrder Check						
					else:
						print("input y or n") # Error Wrong input
						print(" ")
				else: # if the openorders are not empty
					print("---!No OpenOrders!---")
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
		print(" ")		
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
						print("**SELL** AltWorth HIGHER budget")						
						OrderBidsPrice0  = polo.returnOrderBook()[pair]['bids'][0][0] # Collect highest buyorder (0) price
						OrderBidsAmount0 = polo.returnOrderBook()[pair]['bids'][0][1] # Collect highest buyorder (0) amount
						OrderBidsSum0 = float(OrderBidsAmount0) * float(OrderBidsPrice0) # Calculate highest buyorder BTC Value
						
						if float(AltSellWorth) <= float(OrderBidsSum0): # Sell if highest bid (in BTC) is bigger than AltSellWorth (in BTC)
							# Sell to the highest bid (0)
							print("Do you want to SELL? y or n") 
							user_input = input(": ") # Wait for user input to sell
							if user_input == "n":
								break # input = No so continue Script 
							elif user_input == "y":
								sell = polo.sell(pair, Bid, AltSell) # Make the SellOrder
								print("---!SELL Complete!--- fitted in first Bid")
								break
							else:
								print("input y or n") # Error Wrong input
								print(" ")
							
						else: # Highest BuyOrder (0) is to small, Calculate for 1st & 2nd BuyOrder (0&1)
							print("My AltSELL Order is Bigger than BidsSum0")
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
									print("Do you want to SELL? y or n")
									user_input = input(": ") # Wait for user input to sell
									if user_input == "n":
										break # input = No so continue Script 
									elif user_input == "y":
										print("---!SELL 0 Complete!--- fitted in First Bid")
										print("---!SELL 1 Complete!--- fitted in Second Bid")
										print("---!SELL 2 Complete!--- fitted in Third Bid")
										sell = polo.sell(pair, OrderBidsPrice3, AltSell)  # Make the SellOrder
										print("---!SELL 3 Complete!--- fitted in Fourth Bid")										
										break
									else:
										print("input y or n") # Error Wrong input
										print(" ")									
																	
								else: # Sell to the highest 3 bids (BuyOrders 0,1&2)
									print("Do you want to SELL? y or n")
									user_input = input(": ") # Wait for user input to sell
									if user_input == "n":
										break # input = No so continue Script
									elif user_input == "y":
										print("---!SELL 0 Complete!--- fitted in First Bid")
										print("---!SELL 1 Complete!--- fitted in Second Bid")
										sell = polo.sell(pair, OrderBidsPrice2, AltSell) # Make the SellOrder
										print("---!SELL 2 Complete!--- fitted in Third Bid")										
										break
									else:
										print("input y or n") # Error Wrong input
										print(" ")																	
									
							else: # Sell to the highest 2 bids (BuyOrders 0&1)
								#Input for Sell 0&1
								print("Do you want to SELL? y or n")
								user_input = input(": ") # Wait for user input to sell
								if user_input == "n":
									break # input = No so continue Script
								elif user_input == "y":
									print("---!SELL 0 Complete!--- fitted in First Bid")
									sell = polo.sell(pair, OrderBidsPrice1, AltSell) # Make the SellOrder
									print("---!SELL 1 Complete!--- fitted in Second Bid")										
									break
								else:
									print("input y or n") # Error Wrong input
									print(" ")																	
																				
						break # End SELL part					
					else: # BUY!!! Compare BuyOrder with Available Asks (same Logic as SELL part where sell=buy & bid=ask)
						print("**BUY** AltWorth LOWER budget")
						OrderAsksPrice0  = polo.returnOrderBook()[pair]['asks'][0][0]
						OrderAsksAmount0 = polo.returnOrderBook()[pair]['asks'][0][1]
						OrderAsksSum0 = float(OrderAsksAmount0) * float(OrderAsksPrice0)
						
						if float(AltBuyWorth) <= float(OrderAsksSum0): #Order the OrderBook0 
							#Input for Buy
							print("Do you want to BUY? y or n")
							user_input = input(": ") 
							if user_input == "n":
								break
							elif user_input == "y":								
								buy = polo.buy(pair, Ask, AltBuy)
								print("---!Buy Complete!--- fitted in first Ask")
								break
							else:
								print("input y or n")
								print(" ")
							
						else: #OrderBook0 to small Calculate for Order 0&1
							print("My AltBUY Order is Bigger than AsksSum0")
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
									#Input for Buy 012&3 
									print("Do you want to BUY? y or n")
									user_input = input(": ") 
									if user_input == "n":
										break
									elif user_input == "y":
										print("---!BUY 0 Complete!--- fitted in First Bid")
										print("---!BUY 1 Complete!--- fitted in Second Bid")
										print("---!BUY 2 Complete!--- fitted in Third Bid")
										buy = polo.buy(pair, OrderAsksPrice3, AltBuy)
										print("---!BUY 3 Complete!--- fitted in Fourth Bid")										
										break
									else:
										print("input y or n")
										print(" ")																	
									break
								
								else: #Order the Orderbook 01&2
									#Input for Buy 01&2 
									print("Do you want to BUY? y or n")
									user_input = input(": ") 
									if user_input == "n":
										break
									elif user_input == "y":
										print("---!BUY 0 Complete!--- fitted in First Bid")
										print("---!BUY 1 Complete!--- fitted in Second Bid")
										buy = polo.buy(pair, OrderAsksPrice2, AltBuy)
										print("---!BUY 2 Complete!--- fitted in Third Bid")										
										break
									else:
										print("input y or n")
										print(" ")																	
									break									
							else: #Order the Orderbook 0&1
								#Input for Buy 01&2 
								print("Do you want to BUY? y or n")
								user_input = input(": ") 
								if user_input == "n":
									break
								elif user_input == "y":
									print("---!BUY 0 Complete!--- fitted in First Bid")
									buy = polo.buy(pair, OrderAsksPrice1, AltBuy)
									print("---!BUY 1 Complete!--- fitted in Second Bid")										
									break
								else:
									print("input y or n")
									print(" ")								
								break																			
							break
						break # end BUY part						
				break # end of try
			except:
				backoff("Can not finish the OrderBook")
				exit(1)			
		
		print(" ")
		counter = counter + 1

