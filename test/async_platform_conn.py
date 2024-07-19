import asyncio
import requests as url_requests

bingx_main_url = 'http://platform:5000/bingx'

async def bingx_conn():
    response = url_requests.get(bingx_main_url)

    print("Get BingX (step 1)")

    return response.json()

async def place_order_conn(dbcon, message_id, regex_message):
    place_order_url = bingx_main_url + '/place_order'

    json_data = {
        'dbcon'         : dbcon,
        'message_id'    : message_id,
        'regex_message' : regex_message
    }

    response = url_requests.post(place_order_url, json=json_data)

    print("Order Placed (step 1)")

    return response.json()

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