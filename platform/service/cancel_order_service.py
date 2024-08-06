# place order logic here
import asyncio
import json
import datetime
import math
import traceback
import logging

from platform_api.bingx     import BINGX
from dto.dto_bingx_order    import dtoBingXOrder
from dto.dto_bingx_order_tpsl import dtoBingXOrderTPSL

platform    = "bingx"

async def close_all_order(player_session, coin_pair, side=None):
    response = player_session.close_all_order(coin_pair, side)
    
    return response

async def close_all_position(player_session, coin_pair, side):
    response = player_session.close_all_pos(coin_pair, side)
    
    return response

async def close_order(player_session, coin_pair, order_list):
    response = player_session.close_order(coin_pair, order_list)
    
    return response

async def place_order(player_session, order_list):
    response = player_session.place_order(order_list)
    
    return response

async def get_position(player_session, coin_pair):
    response = player_session.get_position(coin_pair)
    
    return response

async def get_price(player_session, coin_pair):
    response = player_session.get_price(coin_pair).get("data").get("price")
    
    return response

async def get_all_pending(player_session, coin_pair):
    response = player_session.get_all_pending(coin_pair)
    
    return response

# --------------------------------------------------------------

def cancel_all_service(follower_data, coin):
    
    for follower in follower_data:
        player = BINGX(follower["api_key"], follower["api_secret"])
    
        asyncio.run(close_all_order(player, coin))
        
    json_ret = {
        "message" : "Cancel All Order"
    }
        
    return json_ret

def cancel_order_service(follower_data, coin_pair, is_not_tp, result):
    
    # Make Returning Json
    json_ret    = {}
    err_list    = {
        "close_position_wrong_code" : [],
        "close_position_fail"       : [],
        "close_order_wrong_code"    : [],
        "close_order_fail"          : [],
        "placing_sl_error"          : [],
        "close_order_issue"         : []
    }
    
    for follower in follower_data:
        player = BINGX(follower['api_key'], follower['api_secret'])
        
        # Market Out
        buy_sell = "BUY"
        if result["long_short"] == "LONG":
            buy_sell = "SELL"
            
        order_list = []
        
        try:
            if is_not_tp:
                # Cancel Position
                order = asyncio.run(close_all_position(player, coin_pair, result["long_short"]))
                
                if order.get("code") != 0 and order.get("code") != 200:
                    err_list["close_position_wrong_code"].append(f'{follower.get("player_id")} with message: {order.get("msg")}')
                
                elif order.get("data") and order.get("data").get("failed") != None:
                    err_list["close_position_fail"].append(f'{follower.get("player_id")} closing position with id: {order.get("data").get("failed")} failed')

                # Cancel Active order
                order = asyncio.run(close_all_order(player, coin_pair, result["long_short"]))
                
                if order.get("code") != 0 and order.get("code") != 200:
                    err_list["close_order_wrong_code"].append(f'{follower.get("player_id")} with message: {order.get("msg")}')
                
                elif order.get("data") and order.get("data").get("failed") != None:
                    err_list["close_order_fail"].append(f'{follower.get("player_id")} closing order with id: {order.get("data").get("failed")} failed ')
            
            else:
                # Cancel SL order
                sl_id_list      = []
                pending_order   = asyncio.run(get_all_pending(player, coin_pair))
                
                for order in pending_order.get("data").get("orders"):
                    if order.get("type") == "STOP" or order.get("type") == "STOP_MARKET":
                        sl_id_list.append(order.get("orderId"))
                        
                order = asyncio.run(close_order(player, coin_pair, sl_id_list))
                
                if order.get("code") != 0 and order.get("code") != 200:
                    err_list["close_order_wrong_code"].append(f'{follower.get("player_id")} with message: {order.get("msg")}')

                elif order.get("data") and order.get("data").get("failed") != None:
                    err_list["close_order_fail"].append(f'{follower.get("player_id")} closing order with id: {order.get("data").get("failed")} failed')

                # Place new SL
                position = asyncio.run(get_position(player, coin_pair))
                
                if len(position.get("data")) != 0:
                    qty         = float(position.get("data")[0].get("positionAmt"))
                    entry       = float(position.get("data")[0].get("avgPrice"))
                    bingx_dto   = dtoBingXOrderTPSL(coin_pair, "sl", buy_sell, result.get("long_short"), entry, qty)
                    
                    order_list.append(bingx_dto.to_json())
                    
                    order  = asyncio.run(place_order(player, order_list))
                    
                    if order.get("code") != 0 and order.get("code") != 200:
                        err_list["placing_sl_error"].append(f'{follower.get("player_id")} with message: {order.get("msg")}')
                        continue
            
            if not json_ret.get("price"):
                json_ret["price"] = asyncio.run(get_price(player, coin_pair))
                
        except Exception as e:
            try:
                logging.error(traceback.format_exc())
            except Exception as e:
                pass
            err_list["close_order_issue"].append(f'{follower.get("player_id")} having issue: {e} ')
    
    json_ret["err_list"] = err_list
    
    return json_ret
    