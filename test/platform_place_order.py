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
logger_mod      = Logger("Order Placed")
logger          = logger_mod.get_logger()

async def place_order_conn(dbcon, message_id):
    
    print("Place Order Start")
    
    place_order_url = bingx_main_url + '/place_order'        
    
    # Prepare Json Return
    json_ret            = {"message": "Order Placed"}
    json_ret["error"]   = {
        "placing_order_error"       : [], 
        "placing_order_warning"     : [],
    }
    
    result = dbcon.get_order_detail_by_order(message_id) if (dbcon != 0) else sql_conn.get_order_detail_by_order(message_id)
    
    if result is None:
            json_ret["error"]["placing_order_error"].append("Order Detail Not found")
            return json_ret
    
    # Connect DB & Get DB data by message id
    # DB: get the follower of Player (Trader)
    if (dbcon != 0):
        # get api list
        api_pair_list = dbcon.get_followers_api(result["player_id"], platform)
        
        if api_pair_list == None or len(api_pair_list) == 0:
            json_ret["error"]["placing_order_warning"].append("Both Trader and Follower have not set API, actual order execution skipped")
            return json_ret
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
            },
        ]
    
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
    entry_list = [float(x) for x in [result["entry1"], result["entry2"]] if x != -1.0]
    entry_count = len(entry_list)

    # Count number of take profit
    tp_list = [x for x in [result["tp1"], result["tp2"], result["tp3"], result["tp4"]] if x != -1.0]
    tp_num = len(tp_list)

    # Get Coin Info
    coin_pair = result["coinpair"].strip().replace("/","").replace("-","").upper()
    coin_pair = coin_pair[:-4] + "-" + coin_pair[-4:]
    
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

    
    if (dbcon != 0):    
        if (order_id_map):
            dbcon.set_client_order_id(order_id_map, message_id)

    return json_ret

if __name__ == "__main__":
    # Make the variable
    message_id1      = 1259026129658843233
    message_id2      = 1259026123581427723
    player_id       = 696898498888466563 # Trader ID
    dbcon           = 0


    json_return = asyncio.run(place_order_conn(dbcon, message_id2))

    print(json_return)