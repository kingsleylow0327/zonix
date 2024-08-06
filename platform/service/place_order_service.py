# place order logic here
import asyncio
import json
import datetime
import math

from platform_api.bingx     import BINGX
from dto.dto_bingx_order    import dtoBingXOrder

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

async def place_single_order(player_session, order_json):
    # When TP is None, remove it
    if order_json['takeProfit'] == None:
        del order_json['takeProfit']

    order = player_session.place_single_order(order_json)

    return order

def place_order_service(regex_data, follower_data):
    # Declare Variable from regex json
    trader_id               = regex_data['trader_id'] # player id (Trader ID)
    wallet_margin           = regex_data['wallet_margin'] # damage cost (everyone follower be same margin)
    coin_pair               = regex_data['coin_pair']
    long_short              = regex_data['long_short']
    entry_price             = regex_data['entry_price']
    stop_loss               = regex_data['stop_loss']
    take_profit             = regex_data['take_profit']
    trailing_stop_price     = regex_data['trailing_stop_price'] 
    trailing_stop_percent   = regex_data['trailing_stop_percent']
    buy_sell                = regex_data['buy_sell']
    order_link_id           = regex_data['order_link_id']

    # Make Returning Json
    # Returning Json 001
    json_ret_err   = {
        "wallet_connection_error"   : [],
        "lower_wallet_amount"       : [],
        "place_order_error"         : [],
        "server_error"              : [],
        "fail_error"                : [],
    }
    # Returning Json 002
    order_id_map = []
    
    # Loop the follower data
    for follower in follower_data:
        # Call platform API
        platform_session = BINGX(follower['api_key'], follower['api_secret'])
        
        # Check the Wallet Balance with BingX
        try:
            wallet = platform_session.get_wallet().get("data").get("balance").get("availableMargin")
        except:
            json_ret_err['wallet_connection_error'].append(follower['player_id'])
            continue

        if float(wallet) < minimum_wallet:
            json_ret_err['lower_wallet_amount'].append(follower['player_id'])
            continue
        
        # Get the qty
        qty = calculate_qty(wallet, entry_price, stop_loss, wallet_margin)
        qty = math.ceil((qty) * 10000) / 10000
        
        platform_session.order_preset(coin_pair)

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
        
        # Place Order (Async)
        try:
            async_order = asyncio.run(place_single_order(platform_session, bingx_dto.to_json()))

            order = async_order
        except Exception as e:
            json_ret_err["place_order_error"].append({
                "player":   follower['player_id'],
                "message":  str(e)
            })
            continue

        if order == None:
            json_ret_err['server_error'].append(follower['player_id'])
            continue

        if order.get("code") != 0 and order.get("code") != 200:
            json_ret_err["fail_error"].append({
                "player":   follower['player_id'],
                "message":  order.get("msg")
            })
            continue

        order_detail_pair = {
            "player_id"         : follower['player_id'],
            "client_order_id"   : order["data"]["order"]["clientOrderID"],
            "order_id"          : order["data"]["order"]["orderId"]
        }

        order_id_map.append(order_detail_pair)
    
    # Combine the return_json
    return_json = {
        'err_list'      : json_ret_err,
        'order_id_map'  : order_id_map
    }
        
    return return_json