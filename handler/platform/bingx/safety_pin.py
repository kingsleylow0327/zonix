import requests as url_requests

from logger                         import Logger
from handler.platform.bingx.global_setup.platform_config import Config as bingx_config
from handler.platform.bingx.components import coin_pair_format, get_follower_data

platform        = bingx_config().platform
bingx_main_url  = bingx_config().platform_url
logger_mod      = Logger("Order SP")
logger          = logger_mod.get_logger()
# Declare URL
sp_url          = bingx_main_url + '/safety_pin'

def platform_sp(dbcon, order_detail):
    result              = order_detail
    ret_json            = {"msg": "Order Safety Pin"}
    
    ret_json["error"]   = {
        "sp_error"   : [], 
        "sp_warning" : []
    }
    
    ret_follower_data   = get_follower_data(dbcon, result, platform)
    
    if ret_follower_data["status_code"] == 400 :
        ret_json["error"]["sp_error"]    = ret_follower_data["message"]["non-order"]
        ret_json["error"]["sp_warning"]  = ret_follower_data["message"]["api-pair-fail"]
        
        return ret_json
    else:
        follower_data = ret_follower_data["message"]
    
    # Coin Pair and Refer ID
    coin_pair = coin_pair_format(result["coinpair"])
    
    json_data = {
        "follower_data"     : follower_data,
        "coin_pair"         : coin_pair,
        "result"            : {
            "player_id"     : result["player_id"],
            "long_short"    : result["long_short"],
        }
    }
    
    response        = url_requests.post(sp_url, json=json_data)
    response_data   = response.json()
    
    ret_json["error"]['close_order_error']  = response_data['err_list']['close_order_error']
    ret_json["error"]['placing_sl_error']   = response_data['err_list']['placing_sl_error']
    ret_json["error"]['sp_fail']            = response_data['err_list']['sp_fail']
    
    ret_json["price"]   = response_data['price']
    
    return ret_json