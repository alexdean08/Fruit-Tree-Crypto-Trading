##
## exchange.py
## This file contains all relevant information regarding the use of Exchange.
## This includes the class Exchange itself, the Exchange functions, and a 
## function generate_exchage which generates the Exchange.
##

from time import sleep
import robin_stocks.robinhood as r
import cbpro
import requests

# All of the current available exchanges for use
exchanges = ['Coinbase Pro', 'Robinhood']

## Exchange
## An Exchange object represents a crypto exchange and a user's wallet in it
##
## exchange_name - The name of the exchange
## coin - The name of the coin that is being traded
## username - The username of the account in use (not always necessary depending on the exchange)
## passphrase - The passphrase of the account in use (not always necessary depending on the exchange)
## api_key - The api key of the user (not always necessary depending on the exchange)
## api_secret - The secret api key of the user (not always necessary depending on the exchange)
## sandbox - True if using snadbox mode, otherwise False
## balance - The USD balance in the user's wallet
## crypto_balance - The amount of the coin the user owns
class Exchange:

    def __init__(self, _exchange_name, _coin, _username, _passphrase, _api_key, _api_secret, _sandbox):
        self.exchange_name = _exchange_name
        self.coin = _coin
        self.username = _username
        self.passphrase = _passphrase
        self.api_key = _api_key
        self.api_secret = _api_secret
        self.sandbox = _sandbox
        self.crypto_balance = 0

        # Check for valid exchange_name
        exchange_present = False
        for i in exchanges:
            if self.exchange_name == i:
                exchange_present = True
                break
        if not exchange_present:
            print('ERROR: \"' + self.exchange_name + '\" is not a valid exchange name.')
            quit()

        # Login to the specified exchange
        if self.exchange_name == 'Coinbase Pro':
            self.client = cbpro.AuthenticatedClient(self.api_key, self.api_secret, self.passphrase)
            self.account_id = input('What\'s your account ID (ex: 7d0f7d8e-dd34-4d9c-a846-06f431c381ba)?: ')
            self.balance =  self.client.get_account(self.account_id)['available']

            self.public_client = cbpro.PublicClient()
        if self.exchange_name == 'Robinhood':
            try:
                login = r.login(username=self.username, password=self.passphrase, store_session=False)
            except:
                print('Cannot login with the provided credentials.')
                quit()
            self.balance = r.load_account_profile()['portfolio_cash']
        
        # If sandbox is specified, provide how much funding to start with
        if self.sandbox:
            self.balance = float(input('How much funding would you like to start with for this sandbox? '))

    ##
    ## Buy the specified crypto with the amount of money in balance
    ##
    def buy(self):

        # If sandbox, set the crypto balance to the current crypto balance / the bid price of one coin
        # and set the balance to 0
        if self.sandbox:
            self.crypto_balance = self.balance/self.get_price(price_mode='ask')
            self.balance = 0
            return
    
        # Use Coinbase Pro to buy
        if self.exchange_name == 'Coinbase Pro':
            order = self.client.buy(product_id=self.coin+'-USD', order_type='market', funds=self.balance)
            while self.client.get_order(order['id'])['status'] != 'pending':
                sleep(0.2)
            if self.client.get_order(order['id'])['status'] == 'canceled':
                print('ERROR: Buy order canceled')
                quit()
            self.crypto_balance = self.client.get_order(order['id'])['size']
        
        # Use Robinhood to buy
        if self.exchange_name == 'Robinhood':
            r.order_buy_crypto_by_price(self.coin, self.balance)
            coin_placement = 0
            for coin_placement in self.crypto_balance:
                if coin_placement['currency']['code'] == self.coin:
                    break
            self.crypto_balance = float(coin_placement['quantity'])

    ##
    ## Sell the specified crypto with the amount of crypto in crypto_balance
    ##
    def sell(self):
        
        # If sandbox, set the balance to the bid price of one coin * the current crypto balance
        # and set the crypto balance to 0
        if self.sandbox:
            self.balance = self.get_price(price_mode='bid')*self.crypto_balance
            self.crypto_balance = 0
            return

        # Use Coinbase Pro to sell
        if self.exchange_name == 'Coinbase Pro':
            order = self.client.sell(product_id=self.coin+'-USD', order_type='market', size=self.crypto_balance)
            while self.client.get_order(order['id'])['status'] != 'pending':
                sleep(0.2)
            if self.client.get_order(order['id'])['status'] == 'canceled':
                print('ERROR: Sell order canceled')
                quit()
            self.balance =  self.client.get_account(self.account_id)['available']
        
        # Use Robinhood to sell
        if self.exchange_name == 'Robinhood':
            r.order_sell_crypto_by_quantity(self.coin, self.crypto_balance)
            self.balance = r.load_account_profile()['portfolio_cash']

    ##
    ## Get the price of one coin
    ##
    ## @param price_mode
    ##      Specifies if the funcition will return the bid price, ask price, or the mark price
    ##
    ## @return
    ##      The current price of the coin
    ##
    def get_price(self, price_mode='None'):

        # Use Coinbase Pro to get the price
        if self.exchange_name == 'Coinbase Pro':
            if self.sandbox:
                if price_mode == 'bid':
                    return float(self.public_client.get_product_ticker(self.coin+'-USD')['bid'])
                return float(self.public_client.get_product_ticker(self.coin+'-USD')['ask'])
            return float(self.public_client.get_product_ticker(self.coin+'-USD')['price'])
        
        # Use Robinhood to get the price
        if self.exchange_name == 'Robinhood':
            if self.sandbox:
                if price_mode == 'bid':
                    return float(r.get_crypto_quote(self.coin)['bid_price'])
                return float(r.get_crypto_quote(self.coin)['ask_price'])
            return float(r.get_crypto_quote(self.coin)['mark_price'])

        
##
## Generate the exchange
##
## @return
##      The exchange generated
##
def generate_exchange():
    exchange = input('What exchange are you using (Coinbase Pro, Robinhood)? ')
    coin = input('What coin would you like to be trading (Use the shorthand name such as BTC, ETH, SOL)? ')
    username = ''
    passphrase = ''
    api_key = ''
    api_secret = ''


    if exchange == 'Coinbase Pro':
        passphrase = input('What is your passphrase? ')
        api_key = input('What is your API key? ')
        api_secret = input('What is your API secret key? ')
    if exchange == 'Robinhood':
        username = input('What is your email? ')
        passphrase = input('What is your password? ')
    
    # Sandbox
    _sandbox = input('Would you like to run this is sandbox mode (Y/N)? ')
    sandbox = False
    if _sandbox.lower() == 'y' or _sandbox.lower() == 'yes':
        sandbox = True
    elif _sandbox.lower() != 'n' and _sandbox.lower() != 'no':
        print('Invalid sandbox response ')
        quit()

    return Exchange(exchange, coin, username, passphrase, api_key, api_secret, sandbox)

