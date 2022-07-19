##
## condition.py
## This file contains all relevant information regarding the use of TradeConditions.
## This includes the class TradeCondition itself, the TradeCondition functions, and a 
## function generate_and_validate_trade_conditions which generates the TradeConditions.
##

import configparser
import glob


## TradeCondition
## A TradeCondition objects represents either a buy or sell trade condition.
##
## condition_id - The unique ID of the condition
## percent_up - If the price goes up X%, from Y
## price_up - If the price goes up $X, from Y
## from_up - Either from the minimum price in the interval (0), or the minimum price since the time of last trade (1)
## percent_down - If the price goes down X%, from Y
## price_down - If the price goes down $X, from Y
## from_down - Either from the maximum price in the interval (0), or the maximum price since the time of last trade (1)
## interval - The interval being looked at (in seconds)
## next_link - The next TradeCondition that must be exceeded before the current trade condition is analyzed (-1 if no next link)
## in_range - 'True' if the condition can potentially be run or is currently being run, 'False' if the condition can't be run (used for linking TradeConditions)
## is_run - 'True' if the condition is being run or has been run already on this interval, 'False' if otherwise
## A CONDITION CAN ONLY RUN WHEN in_range AND is_run ARE BOTH TRUE
## has_previous - Whether a condition has a condition below itself
class TradeCondition:
    def __init__(self, c_id, prcnt_up, prc_up, frm_up, prcnt_down, prc_down, frm_dn, intrvl, link, previous):
        self.condition_id = c_id
        self.percent_up = 1+(prcnt_up/100)
        self.price_up = prc_up
        self.from_up = frm_up
        self.percent_down = 1-(prcnt_down/100)
        self.price_down = prc_down
        self.from_down = frm_dn
        self.interval = intrvl
        self.next_link = link
        self.in_range = True
        self.is_run = False
        
        self.run = False
        self.has_previous = previous
    
    ##
    ## Custom boolean equal
    ##
    ## @param other
    ##      another TradeCondition to see if it is the same as the current TradeCondition
    ##
    ## @return
    ##      True if the two are the same, False if they aren't
    def __eq__(self, other):
        if type(other).__name__ != 'TradeCondition':
            return False
        if self.condition_id == other.condition_id:
            return True
        return False
    
    ##
    ## Reset in_range and is_run after a trade is complete
    ##
    def reset_availability(self):
        self.in_range = True
        self.is_run = False


##
## Generates and validates the trade conditions that a user creates.
## If all of the trading conditions are created correctly by the user, this
## function returns a list of all of the trading conditions generated.
## Otherwise, it will quit and throw an error.
##
## @param mode
##      Either "buy" or "sell"
##
## @return
##      A list of trading conditions
##
def generate_and_validate_trade_conditions(mode):
    conditions = []
    config = configparser.ConfigParser()
    config.read('TradeConditions/'+mode+'-conditions.conf')
    # NOTE: ^^^ maybe add a try catch here. Causes error for condition with same name, more than one of the same variable in a condition

    # Exits if there are no buy/sell conditions
    if len(config.sections()) == 0:
        print('ERROR: No '+mode+' conditions')
        quit()

    # Goes through every trade condition in the config file
    for condition in config.sections():

        # Variables representing what the TradeCondition object contains.
        percent_up=0
        price_up=0
        from_up=-1
        percent_down=0
        price_down=0
        from_down=-1
        interval=0
        next_link=''

        # Represents if the price/percent up/down element of a trade condition is present
        p_up_present = 0
        p_down_present = 0
        
        # Goes through every value in the trade condition
        for val in config[condition]:
            if val.upper() == 'PERCENT_UP':

                # If there isn't also PRICE_UP present
                if not p_up_present:
                    percent_up=float(config[condition][val])
                    p_up_present=1
                else:
                    print('ERROR: Both PERCENT_UP and PRICE_UP present in '+condition)
                    quit()

            if val.upper() == 'PRICE_UP':

                # If there isn't also PERCENT_UP present
                if not p_up_present:
                    price_up=float(config[condition][val])
                    p_up_present=1
                else:
                    print('ERROR: Both PERCENT_UP and PRICE_UP present in '+condition)
                    quit()

            if val.upper() == 'FROM_UP':
                if config[condition][val] == 'INTERVAL_PRICE':
                    from_up=0
                elif config[condition][val] == 'TRADE_PRICE':
                    from_up=1
                else:
                    print('ERROR: \"'+config[condition][val]+'\" invalid value for FROM_UP in '+condition)
                    quit()
            
            if val.upper() == 'PERCENT_DOWN':

                # If there isn't also PRICE_DOWN present
                if not p_down_present:
                    percent_down=float(config[condition][val])
                    p_down_present=1
                else:
                    print('ERROR: Both PERCENT_DOWN and PRICE_DOWN present in '+condition)
                    quit()
            
            if val.upper() == 'PRICE_DOWN':

                # If there isn't also PERCENT_DOWN present
                if not p_down_present:
                    price_down=float(config[condition][val])
                    p_down_present=1
                else:
                    print('ERROR: Both PERCENT_DOWN and PRICE_DOWN present in '+condition)
                    quit()
            
            if val.upper() == 'FROM_DOWN':
                if config[condition][val] == 'INTERVAL_PRICE':
                    from_down=0
                elif config[condition][val] == 'TRADE_PRICE':
                    from_down=1
                else:
                    print('ERROR: \"'+config[condition][val]+'\" invalid value for FROM_DOWN in '+condition)
                    quit()
            
            if val.upper() == 'INTERVAL':
                interval=float(config[condition][val])
            
            if val.upper() == 'NEXT_LINK':
                next_link=config[condition][val]

                # If the next_link referenced doesn't exist
                if not config.has_section(next_link):
                    print('ERROR: In trade condition ' + condition + ', no trade condition with the ID ' + next_link)
                    quit()
                
                # If the next_link referenced is itself
                if condition.lower() == config[condition][val].lower():
                    print('ERROR: In trade condition ' + condition + ', invalid NEXT_LINK. NEXT_LINK cannnot be itself.')
                    quit()

        # Now gathering the variable assignments is done, but still need to check for more errors
        
        # Check for specific values of buy conditions
        if mode == 'buy':

            # If neither PRICE_UP or PERCENT_UP is present, throw an error
            if not p_up_present:
                print('ERROR: No PRICE_UP or PERCENT_UP in condition ' + condition)
                quit()

            # If there are conditions for a next link but nothing is provided for NEXT_LINK, throw an error
            if (from_down > 0 or p_down_present) and not config[condition].get('next_link'):
                print('ERROR: No NEXT_LINK prodvided in condition '+condition+' even though next link conditions are provided')
                quit()

            # If there are no conditions for a next link but NEXT_LINK is provided, throw an error
            if (from_down < 0 or not p_down_present) and config[condition].get('next_link'):
                print('ERROR: NEXT_LINK prodvided in condition '+condition+' but no next link conditions are provided')
                quit()
        
        # Check for specific values of sell conditions
        elif mode == 'sell':

            # If neither PRICE_DOWN or PERCENT_DOWN is present, throw an error
            if not p_down_present:
                print('ERROR: No PRICE_DOWN or PERCENT_DOWN in condition ' + condition)
                quit()

            # If there are conditions for a next link but nothing is provided for NEXT_LINK, throw an error
            if (from_up > 0 or p_up_present) and not config[condition].get('next_link'):
                print('ERROR: No NEXT_LINK prodvided in condition '+condition+' even though next link conditions are provided')
                quit()

            # If there are no conditions for a next link but NEXT_LINK is provided, throw an error
            if (from_up < 0 or not p_up_present) and config[condition].get('next_link'):
                print('ERROR: NEXT_LINK prodvided in condition '+condition+' but no next link conditions are provided')
                quit()
        
        # If there is no interval when there should be
        if (from_up == 0 or from_down == 0) and interval <= 0:
            print('ERROR: Invalid or nonexistant interval for condition ' + condition)
            print('       or invalid use of FROM_UP and/or FROM_DOWN')
            quit()

        # If there is an interval but it isn't needed
        if (from_up != 0 and from_down != 0) and interval > 0:
            print('ERROR: INTERVAL is assigned when it is never needed in condition ' + condition)
            print('       (the condition only uses TRADE_PRICE)')
            quit()

        # See what trade conditions have another trade condition with it as a next link
        has_previous = 0
        for temp_condition in config.sections():
            if config[temp_condition].get('next_link') == condition:
                has_previous = 1
                break
        
        # Everything is correct, so add this condition to the main conditions list
        conditions.append(TradeCondition(condition, percent_up, price_up, from_up, percent_down, price_down, from_down, interval, next_link, has_previous))

    #
    # Done adding trade conditions
    #

    # Makes the next_links actual TradeCondition objects
    for condition in conditions:
        if condition.next_link != '':
            for next_condition in conditions:
                if condition.next_link == next_condition.condition_id:
                    condition.next_link = next_condition
                    break

    # Ensures there aren't any trade condition loops
    for condition in conditions:
        looping_condition = condition
        end_of_loop = 0
        while not end_of_loop:
            if looping_condition.next_link != '':
                looping_condition = looping_condition.next_link
                if looping_condition == condition:
                    print('ERROR: Looping trade conditions')
                    quit()
            else:
                end_of_loop = 1

    # Everything is correct. Return the generated conditions
    return conditions

def generate_sell_floor():
    prompt_sell_floor = input('Would you like to add a sell floor? (Y/N) ')
    if prompt_sell_floor.lower() == 'y' or prompt_sell_floor.lower() == 'yes':
        return float(input('At what price should the floor be at? '))
    else:
        return 0