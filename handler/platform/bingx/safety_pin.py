import requests as url_requests

from logger                         import Logger
from global_setup.platform_config   import Config as bingx_config

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
    
    if result is None:
        ret_json["error"]["sp_error"].append("Order Detail Not found")
        return ret_json
    
     # get api list
    api_pair_list = dbcon.get_followers_api(result["player_id"], platform)
        
    if api_pair_list == None or len(api_pair_list) == 0:
        ret_json["error"]["sp_warning"].append("Both Trader and Follower have not set API, actual order execution skipped")
        return ret_json

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
    coin_pair = result["coinpair"].strip().replace("/","").replace("-","").upper()
    coin_pair = coin_pair[:-4] + "-" + coin_pair[-4:]
    
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