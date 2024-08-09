import requests as url_requests

from logger import Logger
from handler.platform.bingx.global_setup.platform_config import Config as bingx_config
from handler.platform.bingx.components import coin_pair_format, get_follower_data

platform        = bingx_config().platform
bingx_main_url  = bingx_config().platform_url
logger_mod      = Logger("Place Order")
logger          = logger_mod.get_logger()
# Declare URL
place_order_url = bingx_main_url + '/place_order'

def platform_place_order(dbcon, message_id):
    # Prepare Json Return
    json_ret            = {"message": "Order Placed"}
    json_ret["error"]   = {
        "placing_order_error"       : [], 
        "placing_order_warning"     : [],
    }
    
    result              = dbcon.get_order_detail_by_order(message_id)
    ret_follower_data   = get_follower_data(dbcon, result, platform)
    
    if ret_follower_data["status_code"] == 400 :
        json_ret["error"]["placing_order_error"]    = ret_follower_data["message"]["non-order"]
        json_ret["error"]["placing_order_warning"]  = ret_follower_data["message"]["api-pair-fail"]
        
        return json_ret
    else:
        follower_data = ret_follower_data["message"]
    
    # Count number of Entry Point
    entry_list  = [float(x) for x in [result["entry1"], result["entry2"]] if x != -1.0]
    entry_count = len(entry_list)

    # Count number of take profit
    tp_list     = [x for x in [result["tp1"], result["tp2"], result["tp3"], result["tp4"]] if x != -1.0]
    tp_num      = len(tp_list)

    # Get Coin Info
    coin_pair = coin_pair_format(result["coinpair"])
    
    order_id_map = []
    
    json_data = {
        'follower_data' : follower_data,
        'coin_pair'     : coin_pair,
        'result'        : {
            'long_short'        : result["long_short"],   
            'stop_loss'         : result["stop"],
            'order_refer_id'    : result["order_link_id"]
        },
        'entry'         : {
            'entry_list'        : entry_list,   
            'entry_count'       : entry_count,
        },
        'tp'            : {
            'tp_list'           : tp_list,   
            'tp_num'            : tp_num,
        }
    }
    
    # Run the URL & get the response data
    response        = url_requests.post(place_order_url, json=json_data)
    
    response_data   = response.json()
    order_id_map    = response_data['order_id_map']
    
    json_ret["error"]['wallet_error']               = response_data['err_list']['wallet_error']
    json_ret["error"]['async_place_order_error']    = response_data['err_list']['async_place_order_error']

    if (order_id_map):
        dbcon.set_client_order_id(order_id_map, message_id)

    return json_ret