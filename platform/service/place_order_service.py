# place order logic here
import asyncio
import json
import datetime
import math

from platform_api.bingx     import BINGX
from dto.dto_bingx_order    import dtoBingXOrder
from async_collection       import place_order, get_wallet, order_preset

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

def place_order_service(follower_data, coin_pair, result, entry_arr, tp_arr):
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
        player_session = BINGX(follower['api_key'], follower['api_secret'])
        
        try:
            wallet = asyncio.run(get_wallet(player_session))
        except:
            err_list["wallet_error"].append(f'{follower.get("player_id")} with message: Failed to get Wallet, please check API and Secret')
            continue
        
        if float(wallet) < minimum_wallet:
            err_list["wallet_error"].append(f'{follower.get("player_id")} with message: Wallet Amount is lesser than {minimum_wallet}')
            continue
        
        asyncio.run(order_preset(player_session, coin_pair))
        
        counter         = 1
        buy_sell        = "SELL" if (result["long_short"] == "SHORT") else "BUY"
            
        average_entry   = sum(entry_arr['entry_list'])/ float(entry_arr['entry_count'])
        
        for entry in entry_arr['entry_list']:
            order_list  = []
            
            for tp in tp_arr['tp_list']:
                # 3 decimal place
                qty             = calculate_qty(wallet, average_entry, result['stop_loss'], follower.get("damage_cost")) / float(entry_arr['entry_count']) / float(tp_arr["tp_num"])
                qty             = math.ceil((qty) * 10000) / 10000
                order_link_id   = f'{result["order_refer_id"]}-{str(counter)}'
                
                bingx_dto       = dtoBingXOrder(
                    coin_pair,
                    "LIMIT",
                    buy_sell,
                    result["long_short"],
                    entry,
                    qty,
                    tp,
                    qty,
                    result['stop_loss'],
                    qty,
                    order_link_id
                )
                
                counter += 1
                order_list.append(bingx_dto.to_json())
            
            try:
                order = asyncio.run(place_order(player_session, order_list))
            except Exception as e:
                err_list["async_place_order_error"].append(f'{follower.get("player_id")} with message: {e}')
                continue

            if order == None:
                err_list["async_place_order_error"].append(f'{follower.get("player_id")} server error')
                continue

            if order.get("code") != 0 and order.get("code") != 200:
                err_list["async_place_order_error"].append(f'{follower.get("player_id")} with message: {order.get("msg")}')
                continue

            for item in order["data"]["orders"]:
                order_detail_pair = {
                    "player_id"         : follower.get("player_id"),
                    "client_order_id"   : item.get("clientOrderID"),
                    "order_id"          : item.get("orderId")
                }
                
                order_id_map.append(order_detail_pair)
    
    # Combine the return_json
    return_json = {
        'err_list'      : err_list,
        'order_id_map'  : order_id_map
    }
        
    return return_json