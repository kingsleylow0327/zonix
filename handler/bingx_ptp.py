import traceback
import decimal
from bingx.bingx import BINGX
from logger import Logger
from dto.dto_bingx_order import dtoBingXOrder
from dto.dto_bingx_order_tpsl import dtoBingXOrderTPSL

# Logger setup
logger_mod = Logger("Cancel Order")
logger = logger_mod.get_logger()
platform = "bingx"

def h_bingx_ptp(dbcon, order_detail):
    result = order_detail
    ret_json = {"msg": "Order Cancelled"}
    ret_json["error"] = []
    if result is None:
        ret_json["error"].append("Error [PTP]: Order Detail Not found")
        return ret_json
    
    # get api list
    api_pair_list = dbcon.get_followers_api(result["player_id"], platform)
    if api_pair_list == None or len(api_pair_list) == 0:
        ret_json["error"].append("Warning [PTP]: Both Trader and Follower have not set API, actual order execution skipped")
        return ret_json

    session_list = [{"session":BINGX(x["api_key"], x["api_secret"]),
        "role": x["role"], "player_id": x["follower_id"]} for x in api_pair_list]
    
    # Coin Pair and Refer ID
    coin_pair = result["coinpair"].strip().replace("/","").replace("-","").upper()
    coin_pair = coin_pair[:-4] + "-" + coin_pair[-4:]
    coin_info = None
    for item in session_list:
        player = item["session"]
        if coin_info == None:
            coin_info = player.get_coin_info(coin_pair).get("data")[0]
        d = decimal.Decimal(str(coin_info.get("tradeMinQuantity")))
        d = d.as_tuple().exponent * -1
        # Market Out half
        buy_sell = "BUY"
        if result["long_short"] == "LONG":
            buy_sell = "SELL"
        try:
            # Get current coin's amount
            amt = entry = 0
            pos_ret = player.get_position(coin_pair)
            # If error, skip
            if pos_ret.get("code") != 0:
                ret_json["error"].append(f'Error [PTP]: {item.get("player_id")} having issue: {pos_ret.get("msg")} ')
                continue
            position_list = pos_ret.get("data")
            for position in position_list:
                if position.get("positionSide") == result["long_short"]:
                    amt = float(position.get("positionAmt"))
                    entry = float(position.get("avgPrice"))
            if amt == 0 or entry == 0:
                ret_json["error"].append(f'Error [PTP]: {item.get("player_id")} didnt hold any position or entry ')
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
            order = player.place_order([bingx_dto.to_json()])
            if order.get("code") != 0:
                ret_json["error"].append(f'Error [PTP]: {item.get("player_id")} having issue: {order.get("msg")} ')
            
            half_qty = amt - half_qty
            # Cancel pending
            tp_id_list = []
            pending_order = player.get_all_pending(coin_pair)
            for order in pending_order.get("data").get("orders"):
                # need to test for 3 tp sl, if not, also need to remove sl
                if order.get("positionSide") == result["long_short"] and (order.get("type") in ["STOP_MARKET", "STOP", "TAKE_PROFIT_MARKET", "TAKE_PROFIT"]):
                    tp_id_list.append(order.get("orderId"))
            order = player.close_order(coin_pair, tp_id_list)
            if order.get("code") != 0 and order.get("code") != 200:
                ret_json["error"].append(f'Error [Close Order]: {item.get("player_id")} with message: {order.get("msg")}')
            
            # Place new TP and SL
            order_list = []
            tp_list = [x for x in [result["tp1"], result["tp2"], result["tp3"], result["tp4"]] if x != -1.0]
            tp_num = len(tp_list)
            tp_amt = round(half_qty / tp_num, d)
            tp_amt_list = []
            for i in range(tp_num):
                if i == tp_num - 1:
                    tp_amt_list.append(round(half_qty - (tp_amt * (tp_num - 1)), d))
                    continue
                tp_amt_list.append(tp_amt)
            
            # Placing stoploss
            bingx_dto = dtoBingXOrderTPSL(coin_pair, "sl", buy_sell, result.get("long_short"), entry, amt/2)
            order = player.place_single_order(bingx_dto.to_json())
            if order.get("code") != 0 and order.get("code") != 200:
                ret_json["error"].append(f'Error [Placing SL]: {item.get("player_id")} with message: {order.get("msg")}')
            
            # Placing TP
            for i in range(tp_num):
                bingx_dto = dtoBingXOrderTPSL(coin_pair, "tp", buy_sell, result.get("long_short"), tp_list[i], tp_amt_list[i])
                order = player.place_single_order(bingx_dto.to_json())
                if order.get("code") != 0 and order.get("code") != 200:
                    ret_json["error"].append(f'Error [Placing TP]: {item.get("player_id")} with message: {order.get("msg")}')

        except Exception as e:
            try:
                logger.error(traceback.format_exc())
            except Exception as e:
                pass
            ret_json["error"].append(f'Error [PTP]: {item.get("player_id")} having issue: {e} ')
    return ret_json
