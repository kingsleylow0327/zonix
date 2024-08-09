# place order logic here
import asyncio
import json
import datetime
import math

from platform_api.bingx     import BINGX
from dto.dto_bingx_order    import dtoBingXOrder
from async_collection       import place_single_order, get_wallet, order_preset

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

def strategy_order_service(regex_data, follower_data):
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
    err_list   = {
        "wallet_error"              : [],
        "async_place_order_error"   : [],
    }
    
    # Returning Json 002
    order_id_map = []
    
    # Loop the follower data
    for follower in follower_data:
        # Call platform API
        player_session = BINGX(follower['api_key'], follower['api_secret'])
        
        # Check the Wallet Balance with BingX
        try:
            wallet = asyncio.run(get_wallet(player_session))
        except:
            err_list["wallet_error"].append(f'{follower.get("player_id")} with message: Failed to get Wallet, please check API and Secret')
            continue

        if float(wallet) < minimum_wallet:
            err_list["wallet_error"].append(f'{follower.get("player_id")} with message: Wallet Amount is lesser than {minimum_wallet}')
            continue
        
        # Get the qty
        qty = calculate_qty(wallet, entry_price, stop_loss, wallet_margin)
        qty = math.ceil((qty) * 10000) / 10000
        
        asyncio.run(order_preset(player_session, coin_pair))

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
            order_json = bingx_dto.to_json()
            
            # When TP is None, remove it
            if order_json['takeProfit'] == None:
                del order_json['takeProfit']
            
            order = asyncio.run(place_single_order(player_session, order_json))
            
        except Exception as e:
            err_list["async_place_order_error"].append(f'{follower.get("player_id")} with message: {e}')
            continue

        if order == None:
            err_list["async_place_order_error"].append(f'{follower.get("player_id")} server error')
            continue

        if order.get("code") != 0 and order.get("code") != 200:
            err_list["async_place_order_error"].append(f'{follower.get("player_id")} with message: {order.get("msg")}')
            continue

        order_detail_pair = {
            "player_id"         : follower['player_id'],
            "client_order_id"   : order["data"]["order"]["clientOrderID"],
            "order_id"          : order["data"]["order"]["orderId"]
        }

        order_id_map.append(order_detail_pair)
    
    # Combine the return_json
    return_json = {
        'err_list'      : err_list,
        'order_id_map'  : order_id_map
    }
        
    return return_json