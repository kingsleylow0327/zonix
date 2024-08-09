import asyncio
import requests as url_requests
import sys
import os

# Get the parent directory
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(parent_dir)

from sql_con    import ZonixDB
from logger     import Logger
from config     import Config

config          = Config()
platform        = "bingx"
bingx_main_url  = 'http://platform:5000/bingx'
sql_conn        = ZonixDB(config)

# Logger setup
logger_mod      = Logger("Order PTP")
logger          = logger_mod.get_logger()


async def ptp_conn(dbcon, order_detail):
    
    ptp_url = bingx_main_url + '/partial_take_profit'
    
    result              = order_detail
    ret_json            = {"msg": "Order PTP"}
    
    ret_json["error"]   = {
        "ptp_error"   : [], 
        "ptp_warning" : []
    }
    
    if result is None:
        ret_json["error"]["ptp_error"].append("Order Detail Not found")
        return ret_json
    
    if (dbcon != 0):
        # get api list
        api_pair_list = dbcon.get_followers_api(result["player_id"], platform)
        
        if api_pair_list == None or len(api_pair_list) == 0:
            ret_json["error"]["ptp_warning"].append("Both Trader and Follower have not set API, actual order execution skipped")
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
    
if __name__ == "__main__":
    # Make the variable
    order_message_id        = 1259026123581427723
    dbcon                   = 0
    order_detail            = sql_conn.get_order_detail_by_order(order_message_id)
    is_not_tp               = True
    
    coin_pair       = "BTCUSDT"
    coin_pair       = coin_pair.strip().replace("/","").replace("-","").upper()
    coin_pair       = coin_pair[:-4] + "-" + coin_pair[-4:]

    json_return = asyncio.run(ptp_conn(dbcon, order_detail))

    print(json_return)
    