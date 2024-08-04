import asyncio
import requests as url_requests
import datetime
import math

bingx_main_url = 'http://platform:5000/bingx'

async def bingx_conn():
    response = url_requests.get(bingx_main_url)

    print("Get BingX (step 1)")

    return response.json()

async def place_order_conn(dbcon, message_id, regex_message):
    
    print("Order Func Start 001")
    
    place_order_url = bingx_main_url + '/place_order'
    
    # Declare Variable from regex json
    trader_id               = regex_message['strategy'] # player id (Trader ID)
    wallet_margin           = regex_message['margin'] # damage cost (everyone follower be same margin)
    coin_pair               = regex_message['coin_pair']
    long_short              = regex_message['order_action']
    entry_price             = regex_message['entry1']
    stop_loss               = regex_message['stop_lost']
    take_profit             = regex_message['take_profit']
    trailing_stop_price     = regex_message['trailing_stop_price'] 
    trailing_stop_percent   = regex_message['trailing_stop_percentage']
    buy_sell                = "BUY" if long_short == "LONG" else "SHORT"
    order_link_id           = datetime.datetime.now().strftime("%y%m%d%H%M%S") + '-' + coin_pair + '-' + str(trader_id)[-4:]

    # Change Coin Pair Format
    coin_pair       = coin_pair.strip().replace("/","").replace("-","").upper()
    coin_pair       = coin_pair[:-4] + "-" + coin_pair[-4:]
    
    print(order_link_id)
    print(coin_pair)

    # Run async sample
    json_ret            = {"message": "Order Placed"}

    json_ret["error"]   = {
        "api_setup_error"           : [], 
        "wallet_connection_error"   : [],
        "lower_wallet_amount"       : [],
        "place_order_error"         : [],
        "server_error"              : [],
        "fail_error"                : [],
    }
    
    # Connect DB & Get DB data by message id
    # DB: get the follower of Player (Trader)
    if (dbcon != 0):
        api_pair_list       = dbcon.get_followers_api(trader_id, platform)
        
        if api_pair_list == None or len(api_pair_list) == 0:
            # json_ret["error"].append("Warning [Placing Order]: Both Trader and Follower have not set API, actual order execution skipped")
            json_ret["error"]['api_setup_error'].append({
                "message":  "Both Trader and Follower have not set API, actual order execution skipped"
            })
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
            # {
            #     'player_id'     : '706898498888466563',
            #     'follower_id'   : 'player 004',
            #     'api_key'       : 'CghSXMMARbq8zIlVvoCUHwliqu5dHifpzTLZtKkhYDvmrRI8DLgOCGHrCSQr05JfYw10a3vt3wyLoYfyhdvew',
            #     'api_secret'    : 'SiFApEd9EAOv71TXbU47VFP2g1eLR3dyZ5qJ2b7PXR5D0AwSBYjNG3dZkkBtbXEo2DgU2fJNEIGof8rZqk3Y7g',
            #     'role'          : '',
            #     'damage_cost'   : '1',
            # },
        ]
    
    # Prepare the db list which data from DB
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
    
    json_data = {
        'message_id'    : message_id,
        'follower_data' : follower_data,
        'regex_data'    : {
            'trader_id'             : trader_id,
            'wallet_margin'         : wallet_margin,
            'coin_pair'             : coin_pair,
            'long_short'            : long_short,
            'entry_price'           : entry_price,
            'stop_loss'             : stop_loss,
            'take_profit'           : take_profit,
            'trailing_stop_price'   : trailing_stop_price,
            'trailing_stop_percent' : trailing_stop_percent,
            'buy_sell'              : buy_sell,
            'order_link_id'         : order_link_id
        }
    }
    
    # print(json_data)
    
    response        = url_requests.post(place_order_url, json=json_data)
    
    response_data   = response.json()
    
    order_id_map = response_data['order_id_map']
    
    print(response_data)
    
    print("Order Placed (step 1)")
    
    json_ret["error"]['wallet_connection_error']    = response_data['err_list']['wallet_connection_error']
    json_ret["error"]['lower_wallet_amount']        = response_data['err_list']['lower_wallet_amount']
    json_ret["error"]['place_order_error']          = response_data['err_list']['place_order_error']
    json_ret["error"]['server_error']               = response_data['err_list']['server_error']
    json_ret["error"]['fail_error']                 = response_data['err_list']['fail_error']

    
    if (dbcon != 0):    
        if (order_id_map):
            dbcon.set_client_order_id(order_id_map, message_id)

    return json_ret

if __name__ == "__main__":
    # Make the variable
    message_id      = 1259026129658843233
    player_id       = 696898498888466563 # Trader ID
    dbcon           = 0

    regex_message   = {
        "strategy"                  : 696898498888466563, 
        "margin"                    : 1, 
        "coin_pair"                 : "BTCUSDT",
        "order_action"              : "LONG", 
        "entry1"                    : 52000, 
        "stop_lost"                 : 48000,  
        "take_profit"               : 72000, 
        "trailing_stop_price"       : 62000,  
        "trailing_stop_percentage"  : 5, 
    }


    json_return = asyncio.run(place_order_conn(dbcon, message_id, regex_message))

    print(json_return)