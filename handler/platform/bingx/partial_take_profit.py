import requests as url_requests

from logger                         import Logger
from handler.platform.bingx.global_setup.platform_config import Config as bingx_config
from handler.platform.bingx.components import coin_pair_format, get_follower_data

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
    
    ret_follower_data   = get_follower_data(dbcon, result, platform)
    
    if ret_follower_data["status_code"] == 400 :
        ret_json["error"]["ptp_error"]    = ret_follower_data["message"]["non-order"]
        ret_json["error"]["ptp_warning"]  = ret_follower_data["message"]["api-pair-fail"]
        
        return ret_json
    else:
        follower_data = ret_follower_data["message"]
    
    # Coin Pair and Refer ID
    coin_pair = coin_pair_format(result["coinpair"])
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
 
    