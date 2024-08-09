import requests as url_requests

from logger                         import Logger
from global_setup.platform_config   import Config as bingx_config

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
    
    result = dbcon.get_order_detail_by_order(message_id)
    
    if result is None:
        json_ret["error"]["placing_order_error"].append("Order Detail Not found")
        return json_ret
    
    # get api list
    api_pair_list = dbcon.get_followers_api(result["player_id"], platform)
        
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
    
    # Count number of Entry Point
    entry_list  = [float(x) for x in [result["entry1"], result["entry2"]] if x != -1.0]
    entry_count = len(entry_list)

    # Count number of take profit
    tp_list     = [x for x in [result["tp1"], result["tp2"], result["tp3"], result["tp4"]] if x != -1.0]
    tp_num      = len(tp_list)

    # Get Coin Info
    coin_pair   = result["coinpair"].strip().replace("/","").replace("-","").upper()
    coin_pair   = coin_pair[:-4] + "-" + coin_pair[-4:]
    
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