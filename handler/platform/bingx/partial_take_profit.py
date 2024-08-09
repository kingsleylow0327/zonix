import requests as url_requests

from logger                         import Logger
from global_setup.platform_config   import Config as bingx_config

platform        = bingx_config().platform
bingx_main_url  = bingx_config().platform_url
logger_mod      = Logger("Order PTP")
logger          = logger_mod.get_logger()
# Declare URL
ptp_url = bingx_main_url + '/partial_take_profit'

def platform_ptp(dbcon, order_detail):
    result              = order_detail
    ret_json            = {"msg": "Order PTP"}
    
    ret_json["error"]   = {
        "ptp_error"   : [], 
        "ptp_warning" : []
    }
    
    if result is None:
        ret_json["error"]["ptp_error"].append("Order Detail Not found")
        return ret_json
    
    # get api list
    api_pair_list = dbcon.get_followers_api(result["player_id"], platform)
        
    if api_pair_list == None or len(api_pair_list) == 0:
        ret_json["error"]["ptp_warning"].append("Both Trader and Follower have not set API, actual order execution skipped")
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
    coin_info = None
    
    json_data = {
        "follower_data"     : follower_data,
        "coin_pair"         : coin_pair,
        "coin_info"         : coin_info,
        "result"            : {
            "player_id"     : result["player_id"],
            "long_short"    : result["long_short"],
            "tp1"           : result["tp1"],
            "tp2"           : result["tp2"],
            "tp3"           : result["tp3"],
            "tp4"           : result["tp4"],
            "stop"          : result["stop"],
        }
    }
    
    response        = url_requests.post(ptp_url, json=json_data)
    response_data   = response.json()
    
    ret_json["error"]['async_ptp_error']    = response_data['err_list']['async_ptp_error']
    ret_json["error"]['close_order_error']  = response_data['err_list']['close_order_error']
    ret_json["error"]['placing_sl_error']   = response_data['err_list']['placing_sl_error']
    ret_json["error"]['placing_tp_error']   = response_data['err_list']['placing_tp_error']
    ret_json["error"]['ptp_fail']           = response_data['err_list']['ptp_fail']
    
    
    return ret_json
 
    