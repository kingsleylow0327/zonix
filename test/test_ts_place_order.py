import asyncio
import json
import datetime
import math
import os
import sys

# Get the current script's directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Add parent directory to path
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from bingx.bingx            import BINGX
from dto.dto_bingx_order    import dtoBingXOrder
from logger                 import Logger

# Logger setup
logger_mod  = Logger("Place Order")
logger      = logger_mod.get_logger()

maximum_wallet  = 3000
minimum_wallet  = 300
platform        = "bingx"

def calculate_qty(wallet, entry_price, sl, percentage): 
    wallet = float(wallet)
    if wallet > maximum_wallet:
        wallet = maximum_wallet
    
    price_diff = entry_price - sl
    if price_diff < 0:
        price_diff *= -1
    
    order_margin = wallet * percentage/100
    qty = order_margin/price_diff 
    return qty

async def place_bingx_order(order_json, player_session):
    print("BingX Order Run")

    # When TP is None, remove it
    if order_json['takeProfit'] == None:
        del order_json['takeProfit']

    order = player_session.place_single_order(order_json)

    print("BingX Order Done")

    return order

def place_follower_order(dbcon, message_id, regex_json):

    print("Place Follower Order Run")

    # Declare Variable from regex json
    trader_id               = regex_json['strategy'] # player id (Trader ID)
    wallet_margin           = regex_json['margin'] # damage cost (everyone follower be same margin)
    coin_pair               = regex_json['coin_pair']
    long_short              = regex_json['order_action']
    entry_price             = regex_json['entry1']
    stop_loss               = regex_json['stop_lost']
    take_profit             = regex_json['take_profit']
    trailing_stop_price     = regex_json['trailing_stop_price'] 
    trailing_stop_percent   = regex_json['trailing_stop_percentage']
    buy_sell                = "BUY" if long_short == "LONG" else "SHORT"
    order_link_id           = datetime.datetime.now().strftime("%y%m%d%H%M%S") + '-' + coin_pair + '-' + str(trader_id)[-4:]

    # Change Coin Pair Format
    coin_pair       = coin_pair.strip().replace("/","").replace("-","").upper()
    coin_pair       = coin_pair[:-4] + "-" + coin_pair[-4:]

    # Run async sample
    json_ret            = {"msg": "Order Placed"}

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
            json_ret["error"].append({
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


    session_list = [
        {
            "session"       : BINGX(x.get("api_key"), x.get("api_secret")),
            "role"          : x.get("role"),
            "player_id"     : x.get("follower_id"),
            "damage_cost"   : int(x.get("damage_cost"))
        } 
        for x in api_pair_list
    ]
    
    order_id_map = []

    for player in session_list:
        # Check the Wallet Balance with BingX
        try:
            wallet = player["session"].get_wallet().get("data").get("balance").get("availableMargin")
        except:
            json_ret["error"]['wallet_connection_error'].append(player.get("player_id"))
            continue

        if float(wallet) < minimum_wallet:
            json_ret["error"]['lower_wallet_amount'].append(player.get("player_id"))
            continue

        print(wallet)

        # Get the qty
        qty = calculate_qty(wallet, entry_price, stop_loss, wallet_margin)
        qty = math.ceil((qty) * 10000) / 10000
        
        player["session"].order_preset(coin_pair)

        # Get the Json
        bingx_dto = dtoBingXOrder(
            coin_pair,
            "LIMIT",
            buy_sell,
            long_short,
            entry_price,
            qty,
            take_profit,
            qty,
            stop_loss,
            qty,
            order_link_id
        )

        # Place Order 
        try:
            async_order = asyncio.run(place_bingx_order(bingx_dto.to_json(), player["session"]))

            order = async_order
        except Exception as e:
            json_ret["error"]["place_order_error"].append({
                "player":   player.get("player_id"),
                "message":  str(e)
            })
            continue

        if order == None:
            json_ret["error"]['server_error'].append(player.get("player_id"))
            continue

        print(bingx_dto.to_json())    

        print(order)

        if order.get("code") != 0 and order.get("code") != 200:
            json_ret["error"]["fail_error"].append({
                "player":   player.get("player_id"),
                "message":  order.get("msg")
            })
            continue

        order_detail_pair = {
            "player_id"         : player.get("player_id"),
            "client_order_id"   : order["data"]["order"]["clientOrderID"],
            "order_id"          : order["data"]["order"]["orderId"]
        }

        order_id_map.append(order_detail_pair)

        print(order_id_map)
        

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
        'strategy'                  : 696898498888466563, # Player ID
        'margin'                    : 1, # Percent, Max is 100
        'coin_pair'                 : 'BTCUSDT',
        'order_action'              : 'LONG', # [Long/Short]
        'entry1'                    : 52000, # price
        'stop_lost'                 : 48000, # price (if percent,  need do calculation)
        'take_profit'               : 72000, # price (if percent,  need do calculation), If None is no TP Function
        'trailing_stop_price'       : 62000, # price 
        'trailing_stop_percentage'  : 5, # Percent, Max is 100
    }

    json_return = place_follower_order(dbcon, message_id, regex_message)

    print(json_return)