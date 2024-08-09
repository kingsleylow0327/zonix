import requests as url_requests

from logger                         import Logger
from global_setup.platform_config   import Config as bingx_config

platform        = bingx_config().platform
bingx_main_url  = bingx_config().platform_url
logger_mod      = Logger("Cancel Order")
logger          = logger_mod.get_logger()
# Declare URL
cancel_order_url = bingx_main_url + "/cancel_order"

def platform_cancel_all(dbcon, coin, is_active=None):
    player_api_list = dbcon.get_all_player()
    
    follower_data = [
        {
            "api_key"       : x.get("api_key"),
            "api_secret"    : x.get("api_secret"),
        } 
        for x in player_api_list
    ]
    
    json_data = {
        "follower_data"     : follower_data,
        "coin"              : coin,
        "type"              : 1
    }
    
    response        = url_requests.post(cancel_order_url, json=json_data)
    response_data   = response.json()
    
    return response_data

def platform_cancel_order(dbcon, order_detail, is_not_tp=True):
    result              = order_detail
    ret_json            = {"message": "Order Cancelled"}
    ret_json["error"]   = {
        "closing_order_error"   : [], 
        "closing_order_warning" : []
    }
    
    if result is None:
        ret_json["error"]["closing_order_error"].append("Order Detail Not found")
        return ret_json
    
    # get api list
    api_pair_list = dbcon.get_followers_api(result["player_id"], platform)
        
    if api_pair_list == None or len(api_pair_list) == 0:
        ret_json["error"]["closing_order_warning"].append("Both Trader and Follower have not set API, actual order execution skipped")
        return ret_json
    
    # Prepare the db list which data from DB
    follower_data = [
        {
            "api_key"       : x.get("api_key"),
            "api_secret"    : x.get("api_secret"),
            "role"          : x.get("role"),
            "player_id"     : x.get("follower_id")
        } 
        for x in api_pair_list
    ]    
    
    # Coin Pair and Refer ID
    coin_pair       = result["coinpair"].strip().replace("/","").replace("-","").upper()
    coin_pair       = coin_pair[:-4] + "-" + coin_pair[-4:]
    
    json_data = {
        "follower_data"     : follower_data,
        "coin_pair"         : coin_pair,
        "is_not_tp"         : is_not_tp,
        "result"            : {
            'player_id' : result['player_id'],
            'long_short': result['long_short'],    
        },
        "type"              : 0
    }
    
    response        = url_requests.post(cancel_order_url, json=json_data)
    response_data   = response.json()
    
    ret_json["error"]['close_position_wrong_code']  = response_data['err_list']['close_position_wrong_code']
    ret_json["error"]['close_position_fail']        = response_data['err_list']['close_position_fail']
    ret_json["error"]['close_order_wrong_code']     = response_data['err_list']['close_order_wrong_code']
    ret_json["error"]['close_order_fail']           = response_data['err_list']['close_order_fail']
    ret_json["error"]['placing_sl_error']           = response_data['err_list']['placing_sl_error']
    ret_json["error"]['close_order_issue']          = response_data['err_list']['close_order_issue']
    
    ret_json["price"]   = response_data['price']
    
    return ret_json
