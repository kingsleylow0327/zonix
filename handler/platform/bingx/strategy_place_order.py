import datetime
import requests as url_requests

from logger                         import Logger
from handler.platform.bingx.global_setup.platform_config import Config as bingx_config
from handler.platform.bingx.components import coin_pair_format, get_follower_data

platform            = bingx_config().platform
bingx_main_url      = bingx_config().platform_url
logger_mod          = Logger("Place Order")
logger              = logger_mod.get_logger()
# Declare URL
strategy_order_url  = bingx_main_url + '/strategy_place_order'

def platform_strategy_order(dbcon, regex_message, message_id):
    # Declare Variable from regex json
    trader_id               = regex_message['strategy'] # player id (Trader ID)
    wallet_margin           = regex_message['margin'] # damage cost (everyone follower be same margin)
    coin_pair               = regex_message['coin_pair']
    long_short              = regex_message['order_action']
    entry_price             = regex_message['entry_price']
    stop_loss               = regex_message['stop_lost']
    take_profit             = regex_message['take_profit']
    trailing_stop_price     = regex_message['trailing_stop_price'] 
    trailing_stop_percent   = regex_message['trailing_stop_percentage']
    buy_sell                = "BUY" if long_short == "LONG" else "SHORT"
    order_link_id           = datetime.datetime.now().strftime("%y%m%d%H%M%S") + '-' + coin_pair + '-' + str(trader_id)[-4:]

    # Change Coin Pair Format
    coin_pair       = coin_pair_format(coin_pair)
    
    # Prepare Json Return
    json_ret            = {"message": "Strategy Order Placed"}
    json_ret["error"]   = {
        "placing_order_warning"     : [], 
    }
    
    api_pair_list       = dbcon.get_followers_api(trader_id, platform)
        
    if api_pair_list == None or len(api_pair_list) == 0:
        json_ret["error"]["placing_order_warning"].append("Both Trader and Follower have not set API, actual order execution skipped")
        return json_ret

    # Prepare the follower list which data from DB
    follower_data = [
        {
            "api_key"       : x.get("api_key"),
            "api_secret"    : x.get("api_secret"),
            "role"          : x.get("role"),
            "player_id"     : x.get("follower_id"),
            "damage_cost"   : int(x.get("damage_cost"))
        } 
        for x in api_pair_list
    ]
    
    json_data = {
        'follower_data' : follower_data,
        'regex_data'    : {
            'trader_id'             : trader_id,
            'wallet_margin'         : wallet_margin,
            'coin_pair'             : coin_pair,
            'long_short'            : long_short,
            'entry_price'           : entry_price,
            'stop_loss'             : stop_loss,
            'take_profit'           : take_profit,
            'trailing_stop_price'   : trailing_stop_price,
            'trailing_stop_percent' : trailing_stop_percent,
            'buy_sell'              : buy_sell,
            'order_link_id'         : order_link_id
        }
    }
    
    # Run the URL & get the response data
    response        = url_requests.post(strategy_order_url, json=json_data)
    
    response_data   = response.json()
    order_id_map    = response_data['order_id_map']
    
    json_ret["error"]['wallet_error']               = response_data['err_list']['wallet_error']
    json_ret["error"]['async_place_order_error']    = response_data['err_list']['async_place_order_error']

    if (order_id_map):
        dbcon.set_client_order_id(order_id_map, message_id)

    return json_ret