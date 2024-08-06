import asyncio
import requests as url_requests
import logging
import sys
import os

# Get the parent directory
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# Add the parent directory to the system path
sys.path.append(parent_dir)

# Now you can import parent.py

import traceback
from sql_con import ZonixDB
from config import Config

config = Config()

platform = "bingx"

bingx_main_url = 'http://platform:5000/bingx'
sql_conn = ZonixDB(config)

async def cancel_all_conn(dbcon, coin, is_active=None):
    cancel_order_url = bingx_main_url + "/cancel_order"
    
    if (dbcon != 0):
         player_api_list = dbcon.get_all_player()
    else:
        player_api_list = [
            {
                'player_id'     : '696898498888466563',
                'follower_id'   : 'player 001',
                'api_key'       : 'Wc6XS79BfLPHtGKI5I5Jvh6hRCiAadMisrhmhHTtJFlbcWAkX0QVCA2gqE2c18EZO5P1MEF8sdTYPbWIzDkw',
                'api_secret'    : 'fapk3IZ5bcp6ZhQVIiHLt0w2p9LZTm0yO2D9Tr4DYFlczBwxVbXVBpogewiC5pGTgND361lsZ9Q8ZK5fhWNA',
                'role'          : '',
                'damage_cost'   : '1',
            },
            {
                'player_id'     : '706898498888466563',
                'follower_id'   : 'player 002',
                'api_key'       : 'CghSXMMARbq8zIlVvoCUHwliqu5dHifpzTLZtKkhYDvmrRI8DLgOCGHrCSQr05JfYw10a3vt3wyLoYfyhdvew',
                'api_secret'    : 'SiFApEd9EAOv71TXbU47VFP2g1eLR3dyZ5qJ2b7PXR5D0AwSBYjNG3dZkkBtbXEo2DgU2fJNEIGof8rZqk3Y7g',
                'role'          : '',
                'damage_cost'   : '1',
            },
            {
                'player_id'     : '696898498888466563',
                'follower_id'   : 'player 003',
                'api_key'       : 'Wc6XS79BfLPHtGKI5I5Jvh6hRCiAadMisrhmhHTtJFlbcWAkX0QVCA2gqE2c18EZO5P1MEF8sdTYPbWIzDkw',
                'api_secret'    : 'fapk3IZ5bcp6ZhQVIiHLt0w2p9LZTm0yO2D9Tr4DYFlczBwxVbXVBpogewiC5pGTgND361lsZ9Q8ZK5fhWNA',
                'role'          : '',
                'damage_cost'   : '1',
            }
        ]
    
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

async def cancel_order_conn(dbcon, order_detail, is_not_tp=True):
    
    print("Cancel Order Start")
    
    cancel_order_url = bingx_main_url + "/cancel_order"
    
    result              = order_detail
    ret_json            = {"message": "Order Cancelled"}
    ret_json["error"]   = {
        "closing_order_error"   : [], 
        "closing_order_warning" : []
    }
    
    if result is None:
        ret_json["error"]["closing_order_error"].append("Order Detail Not found")
        return ret_json
    
    if (dbcon != 0):
        # get api list
        api_pair_list = dbcon.get_followers_api(result["player_id"], platform)
        
        if api_pair_list == None or len(api_pair_list) == 0:
            ret_json["error"]["closing_order_warning"].append("Both Trader and Follower have not set API, actual order execution skipped")
            return ret_json
    else:
        api_pair_list   = [
            {
                'player_id'     : '696898498888466563',
                'follower_id'   : 'player 001',
                'api_key'       : 'Wc6XS79BfLPHtGKI5I5Jvh6hRCiAadMisrhmhHTtJFlbcWAkX0QVCA2gqE2c18EZO5P1MEF8sdTYPbWIzDkw',
                'api_secret'    : 'fapk3IZ5bcp6ZhQVIiHLt0w2p9LZTm0yO2D9Tr4DYFlczBwxVbXVBpogewiC5pGTgND361lsZ9Q8ZK5fhWNA',
                'role'          : '',
                'damage_cost'   : '1',
            },
            {
                'player_id'     : '706898498888466563',
                'follower_id'   : 'player 002',
                'api_key'       : 'CghSXMMARbq8zIlVvoCUHwliqu5dHifpzTLZtKkhYDvmrRI8DLgOCGHrCSQr05JfYw10a3vt3wyLoYfyhdvew',
                'api_secret'    : 'SiFApEd9EAOv71TXbU47VFP2g1eLR3dyZ5qJ2b7PXR5D0AwSBYjNG3dZkkBtbXEo2DgU2fJNEIGof8rZqk3Y7g',
                'role'          : '',
                'damage_cost'   : '1',
            },
            {
                'player_id'     : '696898498888466563',
                'follower_id'   : 'player 003',
                'api_key'       : 'Wc6XS79BfLPHtGKI5I5Jvh6hRCiAadMisrhmhHTtJFlbcWAkX0QVCA2gqE2c18EZO5P1MEF8sdTYPbWIzDkw',
                'api_secret'    : 'fapk3IZ5bcp6ZhQVIiHLt0w2p9LZTm0yO2D9Tr4DYFlczBwxVbXVBpogewiC5pGTgND361lsZ9Q8ZK5fhWNA',
                'role'          : '',
                'damage_cost'   : '1',
            }
        ]
    
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
    # order_refer_id  = result["order_link_id"]
    
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


if __name__ == "__main__":
    # Make the variable
    order_message_id        = 1259026123581427723
    dbcon                   = 0
    order_detail            = sql_conn.get_order_detail_by_order(order_message_id)
    is_not_tp               = True
    
    coin_pair       = "BTCUSDT"
    coin_pair       = coin_pair.strip().replace("/","").replace("-","").upper()
    coin_pair       = coin_pair[:-4] + "-" + coin_pair[-4:]

    # json_return = asyncio.run(cancel_order_conn(dbcon, order_detail, is_not_tp))
    json_return = asyncio.run(cancel_all_conn(dbcon, coin_pair))

    print(json_return)