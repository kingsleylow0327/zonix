import asyncio
import traceback
import logging
import decimal

from platform_api.bingx         import BINGX
from dto.dto_bingx_order        import dtoBingXOrder
from dto.dto_bingx_order_tpsl   import dtoBingXOrderTPSL
from async_collection           import get_all_pending, get_position, place_order, close_order, get_price

platform    = "bingx"

def sp_service(follower_data, coin_pair, result):
    
    ret_json = {}
    err_list = {
        "close_order_error"     : [],
        "placing_sl_error"      : [],
        "sp_fail"               : [],
    }
    
    for follower in follower_data:
        player      = BINGX(follower["api_key"], follower["api_secret"])
        
        # Market Out
        buy_sell    = "SELL" if (result["long_short"] == "LONG") else "BUY"
        order_list  = []
        
        try:
            sl_id_list      = []
            pending_order   = asyncio.run(get_all_pending(player, coin_pair))
            
            for order in pending_order.get("data").get("orders"):
                if order.get("type") == "STOP" or order.get("type") == "STOP_MARKET":
                    sl_id_list.append(order.get("orderId"))
            
            order   = asyncio.run(close_order(player, coin_pair, sl_id_list))
            
            if order.get("code") != 0 and order.get("code") != 200:
                err_list["close_order_error"].append(f'{follower.get("player_id")} with message: {order.get("msg")}')

            elif order.get("data") and order.get("data").get("failed") != None:
                err_list["close_order_error"].append(f'{follower.get("player_id")} closing order with id: {order.get("data").get("failed")} failed')

            # Place new SL
            position    = asyncio.run(get_position(player, coin_pair))
            
            if len(position.get("data")) != 0:
                qty         = float(position.get("data")[0].get("positionAmt"))
                entry       = float(position.get("data")[0].get("avgPrice"))
                bingx_dto   = dtoBingXOrderTPSL(coin_pair, "sl", buy_sell, result.get("long_short"), entry, qty)
                
                order_list.append(bingx_dto.to_json())
                
                order       = asyncio.run(place_order(player, order_list))
                
                
                if order.get("code") != 0 and order.get("code") != 200:
                    err_list["placing_sl_error"].append(f'{follower.get("player_id")} with message: {order.get("msg")}')
                    continue
            
            if not ret_json.get("price"):
                ret_json["price"] = asyncio.run(get_price(player, coin_pair))
        
        except Exception as e:
            try:
                logging.error(traceback.format_exc())
            except Exception as e:
                pass
            err_list["sp_fail"].append(f'{follower.get("player_id")} having issue: {e} ')
    
    ret_json["err_list"] = err_list
    
    return ret_json