import requests as url_requests

from logger                         import Logger
from handler.platform.bingx.global_setup.platform_config import Config as bingx_config
from handler.platform.bingx.components import coin_pair_format, get_follower_data

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
    
    ret_follower_data   = get_follower_data(dbcon, result, platform)
    
    if ret_follower_data["status_code"] == 400 :
        ret_json["error"]["closing_order_error"]    = ret_follower_data["message"]["non-order"]
        ret_json["error"]["closing_order_warning"]  = ret_follower_data["message"]["api-pair-fail"]
        
        return ret_json
    else:
        follower_data = ret_follower_data["message"]
    
    # Coin Pair and Refer ID
    coin_pair = coin_pair_format(result["coinpair"])
    
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
