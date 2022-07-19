##
## auto-trader.py
## This file is contains the main functionality of the auto-trader.
## It contains the algorithmic trading methodology and generates all of the
## necessary objects.
## The main algorithmic trading functionality is under the large while loop,
## which loops through the trading conditions and sees which ones pass. If so,
## a trade is executed, otherwise it goes to the next trading condition.
##
## The auto-trader can only be in either buying mode or selling mode.
## If you wish to do more at once, run this as many times as you would like simultaneously
##

from time import sleep
import time
import condition
import exchange

##
## Disables the current condition and enables the next condition on the branch
##
## @param _condition
##      The current condition that needs to not be run anymore
##
def next_link(_condition):
    print("NEXT LINK from condition " + _condition.condition_id + " to condition " + _condition.next_link.condition_id)
    _condition.run = False
    _condition.next_link.run = True

# The time in seconds between price retrievals
sleep_time = 0.2

# Generate the crypto exchange
crypto_exchange = exchange.generate_exchange()

# The buy conditions
buy_conditions = condition.generate_and_validate_trade_conditions('buy')

# The sell conditions
sell_conditions = condition.generate_and_validate_trade_conditions('sell')

# The sell floor (sells everything and stops program)
sell_floor = condition.generate_sell_floor()

# Done generating everything, now the auto-trader will run
print('--------------------------------------')
print('           Done configuring')
print('    The auto-trader is now running')
print('--------------------------------------')

# Pair of price and time
prices_interval = []

# MODE:
# 0 - buy
# 1 - sell
mode = 0

# Changes to true after every trade and causes a reset to key variables 
reset = True

# Get the max interval length
max_interval_length = 0
for i in buy_conditions:
    if i.interval > max_interval_length:
        max_interval_length = i.interval

for i in sell_conditions:
    if i.interval > max_interval_length:
        max_interval_length = i.interval

# Declare the variables max_price_since_trade and min_price_since_trade
max_price_since_trade = crypto_exchange.get_price()
min_price_since_trade = max_price_since_trade

#
# The main while loop that goes executes the algorithmic trading
#
while True:
    
    # If a trade has just been executed
    if reset:
        
        # Ensure this section only runs right after a trade is executed 
        reset = False

        # After every trade, the USD balance and crypto balance is printed to Account_Holdings.txt
        account_holdings = open('Account-Holdings.txt', 'a')
        account_holdings.truncate(0)
        account_holdings.write('Current balance in USD: '+str(crypto_exchange.balance)+'\n')
        account_holdings.write('Current balance in '+str(crypto_exchange.coin)+': '+str(crypto_exchange.crypto_balance))
        account_holdings.close()

        # Clear the list of prices in the interval
        prices_interval.clear()

        # Reset max_price_since_trade and min_price_since_trade
        max_price_since_trade = crypto_exchange.get_price()
        min_price_since_trade = max_price_since_trade

        # Reset the availability of the buy conditions
        for i in buy_conditions:
            if not i.has_previous:
                i.run = True
            else:
                i.run = False

        # Reset the availability of the sell conditions
        for i in sell_conditions:
            if not i.has_previous:
                i.run = True
            else:
                i.run = False

    # Pause between getting the prices
    sleep(sleep_time)

    # Get the price of the coin
    crypto_price = crypto_exchange.get_price()

    # Link the price and time of the coin and append it to the interval prices list
    current_time = time.time()
    prices_interval.append((crypto_price, current_time))

    # Remove the prices with a time that are greater than maximum interval seconds ago
    for i in prices_interval:
        if current_time - i[1] > max_interval_length:
            prices_interval.pop(0)
        else:
            break
    
    # If the current price is greater than the max price since the last trade
    if crypto_price > max_price_since_trade:
        max_price_since_trade = crypto_price

    # If the current price is less than the min price since the last trade
    if crypto_price < min_price_since_trade:
        min_price_since_trade = crypto_price

    # If the price is less than the sell floor, sell everything and end the program
    if crypto_price < sell_floor:
        print("PRICE IS BELOW THE SELL FLOOR")
        if mode == 1:
            crypto_exchange.sell()
        quit()

    #
    # BUY MODE
    #
    if mode == 0:

        # Loop through every buy condition
        for i in buy_conditions:
            
            # If the current buy condition isn't valid, move on to the next one
            if not i.run:
                continue
            
            # Get the max and min prices in the interval of the buy condition
            max_interval_price = crypto_price
            min_interval_price = crypto_price
            for p in reversed(prices_interval):
                if current_time - p[1] > i.interval:
                    break
                if p[0] > max_interval_price:
                    max_interval_price = p[0]
                elif p[0] < min_interval_price:
                    min_interval_price = p[0]
            
            # If the buy condition used PERCENT_UP
            if i.percent_up > 1:

                # If the condition uses INTERVAL_PRICE
                if i.from_up == 0:

                    # If the current price >= minimum price in the interval * the percent up, BUY
                    if crypto_price >= (min_interval_price*i.percent_up):
                        print("BOUGHT AT "+str(crypto_price))
                        mode = 1
                        reset = True
                        crypto_exchange.buy()
                
                # If the condition uses TRADE_PRICE
                else:

                    # If the current price >= minimum price since the last trade * the percent up, BUY
                    if crypto_price >= (min_price_since_trade*i.percent_up):
                        print("BOUGHT AT "+str(crypto_price))
                        mode = 1
                        reset = True
                        crypto_exchange.buy()

            # If the buy condition used PRICE_UP
            else:

                # If the condition uses INTERVAL_PRICE
                if i.from_up == 0:

                    # If the current price >= minimum price in the interval + the price up, BUY
                    if crypto_price >= min_interval_price + i.price_up:
                        print("BOUGHT AT "+str(crypto_price))
                        mode = 1
                        reset = True
                        crypto_exchange.buy()

                # If the condition uses TRADE_PRICE
                else:

                    # If the current price >= minimum price since the last trade + the price up, BUY
                    if crypto_price >= min_price_since_trade + i.price_up:
                        print("BOUGHT AT "+str(crypto_price))
                        mode = 1
                        reset = True
                        crypto_exchange.buy()
            
            # If there is no next link, continue to the next buy condition
            if type(i.next_link).__name__ != 'TradeCondition':
                continue

            # If the buy condition uses PERCENT_DOWN
            if i.percent_down < 1:

                # If the condition uses INTERVAL_PRICE
                if i.from_down == 0:

                    # If the current price <= maximum price in the interval * the percent down, NEXT LINK
                    if crypto_price <= (max_interval_price*i.percent_down):
                        next_link(i)
                
                # If the condition uses TRADE_PRICE
                else:

                    # If the current price <= maximum price since the last trade * the percent down, NEXT LINK
                    if crypto_price <= (max_price_since_trade*i.percent_down):
                        next_link(i)
            
            # If the buy condition uses PRICE_DOWN
            else:

                # If the buy condition uses INTERVAL_PRICE
                if i.from_down == 0:

                    # If the difference of the maximum price in the interval and the current price >= the price down, NEXT LINK
                    if (max_interval_price-crypto_price) >= i.price_down:
                        next_link(i)
                
                # If the buy condition uses TRADE_PRICE
                else:

                    # If the difference of the maximum price since the last trade and the current price >= the price down, NEXT LINK
                    if (max_price_since_trade-crypto_price) >= i.price_down:
                        next_link(i)

    #
    # SELL MODE
    #                  
    else:

        # Loop through every sell condition
        for i in sell_conditions:

            # If the current sell condition isn't valid, move on to the next one
            if not i.run:
                continue

            # Get the max and min prices in the interval of the sell condition
            max_interval_price = crypto_price
            min_interval_price = crypto_price
            for p in reversed(prices_interval):
                if current_time - p[1] > i.interval:
                    break
                if p[0] > max_interval_price:
                    max_interval_price = p[0]
                elif p[0] < min_interval_price:
                    min_interval_price = p[0]
            
            # If the sell condition uses PERCENT_DOWN
            if i.percent_down < 1:

                # If the condition uses INTERVAL_PRICE
                if i.from_down == 0:

                    # If the current price <= maximum price in the interval * the percent down, SELL
                    if crypto_price <= (max_interval_price*i.percent_down):
                        print("SOLD AT "+str(crypto_price))
                        mode = 0
                        reset = True
                        crypto_exchange.sell()
                
                # If the condition uses TRADE_PRICE
                else:

                    # If the current price <= maximum price since the last trade * the percent down, SELL
                    if crypto_price <= (max_price_since_trade*i.percent_down):
                        print("SOLD AT "+str(crypto_price))
                        mode = 0
                        reset = True
                        crypto_exchange.sell()
            
            # If the sell condition uses PRICE_DOWN
            else:

                # If the condition uses INTERVAL_PRICE 
                if i.from_down == 0:

                    # If the difference of the maximum price in the interval and the current price >= the price down, SELL
                    if (max_interval_price-crypto_price) >= i.price_down:
                        print("SOLD AT "+str(crypto_price))
                        mode = 0
                        reset = True
                        crypto_exchange.sell()
                
                # If the condition uses TRADE_PRICE
                else:

                    # If the difference of the maximum price since the last trade and the current price >= the price down, SELL
                    if (max_price_since_trade-crypto_price) >= i.price_down:
                        print("SOLD AT "+str(i.price_down))
                        mode = 0
                        reset = True
                        crypto_exchange.sell()

            # If there is no next link, continue to the next sell condition
            if type(i.next_link).__name__ != 'TradeCondition':
                continue
            
            # If the sell condition uses PERCENT_UP
            if i.percent_up > 1:

                # If the condition uses INTERVAL_PRICE
                if i.from_up == 0:

                    # If the current price >= minimum price in the interval * the percent up, NEXT LINK
                    if crypto_price >= (min_interval_price*i.percent_up):
                        next_link(i)
                
                # If the condition uses TRADE_PRICE
                else:

                    # If the current price >= minimum price since the last trade + the percent up, NEXT LINK
                    if crypto_price >= (min_price_since_trade*i.percent_up):
                        next_link(i)
            
            # If the sell condition uses PRICE_UP
            else:

                # If the condition uses INTERVAL_PRICE
                if i.from_up == 0:

                    # If the current price >= minimum price in the interval + the price up, NEXT LINK
                    if crypto_price >= min_interval_price + i.price_up:
                        next_link(i)
                
                # If the condition uses TRADE_PRICE
                else:

                    # If the current price >= minimum price since the last trade + the price up, NEXT LINK
                    if crypto_price >= min_price_since_trade + i.price_up:
                        next_link(i)
                        
