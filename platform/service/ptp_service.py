import asyncio
import traceback
import logging
import decimal

from platform_api.bingx         import BINGX
from dto.dto_bingx_order        import dtoBingXOrder
from dto.dto_bingx_order_tpsl   import dtoBingXOrderTPSL
from async_collection           import get_all_pending, get_position, place_order, close_order, place_single_order, get_coin_info

platform    = "bingx"

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def ptp_service(follower_data, coin_pair, coin_info, result):
    
    err_list = {
        "async_ptp_error"       : [],
        "close_order_error"     : [],
        "placing_sl_error"      : [],
        "placing_tp_error"      : [], 
        "ptp_fail"              : [],
    }
    
    for follower in follower_data:
        player = BINGX(follower["api_key"], follower["api_secret"])
        
        if coin_info == None:
            try:
                coin_info = asyncio.run(get_coin_info(player, coin_pair))
            except Exception as e:
                err_list["ptp_fail"].append(f'{follower.get("player_id")} having issue: Failed to PTP, please check API and Secret ')
                continue
            
        d = decimal.Decimal(str(coin_info.get("tradeMinQuantity")))
        d = d.as_tuple().exponent * -1
        # Market Out half
        buy_sell    = "SELL" if (result["long_short"] == "LONG") else "BUY"
        
        try:
            # Get current coin's amount
            amt     = 0
            pos_ret = asyncio.run(get_position(player, coin_pair))
            
            # If error, skip
            if pos_ret.get("code") != 0:
                err_list["async_ptp_error"].append(f'{follower.get("player_id")} having issue: {pos_ret.get("msg")} ')
                continue
            
            position_list = pos_ret.get("data")
            
            for position in position_list:
                if position.get("positionSide") == result["long_short"]:
                    amt = float(position.get("positionAmt"))
            
            if amt == 0:
                continue
            
            half_qty = round(amt/2, d)
            # TP half (place order)
            bingx_dto = dtoBingXOrder(coin_pair,
                                "MARKET",
                                buy_sell,
                                result["long_short"],
                                0,
                                half_qty,
                                0,
                                0,
                                0,
                                0)
            
            order = asyncio.run(place_order(player, [bingx_dto.to_json()]))
            
            if order.get("code") != 0:
                err_list["async_ptp_error"].append(f'{follower.get("player_id")} having issue: {order.get("msg")} ')
            
            half_qty = amt - half_qty
            
            # Cancel pending
            tp_id_list      = []
            pending_order   = asyncio.run(get_all_pending(player, coin_pair))
            
            for order in pending_order.get("data").get("orders"):
                # need to test for 3 tp sl, if not, also need to remove sl
                if order.get("type") in ["STOP_MARKET", "STOP", "TAKE_PROFIT_MARKET", "TAKE_PROFIT"]:
                    tp_id_list.append(order.get("orderId"))
                    
            order = asyncio.run(close_order(player, coin_pair, tp_id_list))
            
            if order.get("code") != 0 and order.get("code") != 200:
                err_list["close_order_error"].append(f'{follower.get("player_id")} with message: {order.get("msg")}')
            
            # Place new TP and SL
            order_list  = []
            tp_list     = [x for x in [result["tp1"], result["tp2"], result["tp3"], result["tp4"]] if x != -1.0]
            tp_num      = len(tp_list)
            tp_amt      = round(half_qty / tp_num, d)
            tp_amt_list = []
            
            for i in range(tp_num):
                if i == tp_num - 1:
                    tp_amt_list.append(round(half_qty - (tp_amt * (tp_num - 1)), d))
                    continue
                tp_amt_list.append(tp_amt)
            
            # Placing stoploss
            bingx_dto   = dtoBingXOrderTPSL(coin_pair, "sl", buy_sell, result.get("long_short"), result.get("stop"), amt/2)
            order       = asyncio.run(place_single_order(player, bingx_dto.to_json()))
            
            if order.get("code") != 0 and order.get("code") != 200:
                err_list["placing_sl_error"].append(f'{follower.get("player_id")} with message: {order.get("msg")}')
            
            # Placing TP
            for i in range(tp_num):
                bingx_dto   = dtoBingXOrderTPSL(coin_pair, "tp", buy_sell, result.get("long_short"), tp_list[i], tp_amt_list[i])
                order       = asyncio.run(place_single_order(player, bingx_dto.to_json()))
                
                if order.get("code") != 0 and order.get("code") != 200:
                    err_list["placing_tp_error"].append(f'{follower.get("player_id")} with message: {order.get("msg")}')

        except Exception as e:
            try:
                logger.error(traceback.format_exc())
            except Exception as e:
                pass
            err_list["ptp_fail"].append(f'{follower.get("player_id")} having issue: {e} ')
            
    # Combine the return_json
    return_json = {
        'err_list'      : err_list
    }
        
    return return_json