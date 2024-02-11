from bingx.bingx import BINGX
from logger import Logger
from dto.dto_bingx_order import dtoBingXOrder
from dto.dto_bingx_order_tpsl import dtoBingXOrderTPSL

# Logger setup
logger_mod = Logger("Cancel Order")
logger = logger_mod.get_logger()
platform = "bingx"

def h_bingx_cancel_all(dbcon, coin):
    player_api_list = dbcon.get_all_player()
    for i in player_api_list:
        session = BINGX(i["api_key"], i["api_secret"])
        session.close_all_order(coin)
    return "Cancel All Done"

# if is_not_tp is false, it's hit tp and shifting stoploss
def h_bingx_cancel_order(dbcon, order_detail, is_not_tp=True):
    result = order_detail
    ret_json = {"msg": "Order Cancelled"}
    ret_json["error"] = []
    if result is None:
        ret_json["error"].append("Error [Closing Order]: Order Detail Not found")
        return ret_json
    
    # get api list
    api_pair_list = dbcon.get_followers_api(result["player_id"], platform)
    if api_pair_list == None or len(api_pair_list) == 0:
        ret_json["error"].append("Warning [Closing Order]: Both Trader and Follower have not set API, actual order execution skipped")
        return ret_json

    session_list = [{"session":BINGX(x["api_key"], x["api_secret"]),
        "role": x["role"], "player_id": x["follower_id"]} for x in api_pair_list]
    
    # Coin Pair and Refer ID
    coin_pair = result["coinpair"].strip().replace("/","").replace("-","").upper()
    coin_pair = coin_pair[:-4] + "-" + coin_pair[-4:]
    # order_refer_id = result["order_link_id"]
    ret_json = {}
    for item in session_list:
        player = item["session"]
        # Market Out
        buy_sell = "BUY"
        if result["long_short"] == "LONG":
            buy_sell = "SELL"
        order_list = []
        try:
            if is_not_tp:
                # Cancel Position
                order = player.close_all_pos(coin_pair)
                if order.get("code") != 0 and order.get("code") != 200:
                    ret_json["error"].append(f'Error [Close Position]: {item.get("player_id")} with message: {order.get("msg")}')
                
                elif order.get("data") and order.get("data").get("failed") != None:
                    ret_json["error"].append(f'Error [Close Position]: {item.get("player_id")} closing position with id: {order.get("data").get("failed")} failed')

                # Cancel Active order
                order = player.close_all_order(coin_pair)
                if order.get("code") != 0 and order.get("code") != 200:
                    ret_json["error"].append(f'Error [Close Order]: {item.get("player_id")} with message: {order.get("msg")}')
                
                elif order.get("data") and order.get("data").get("failed") != None:
                    ret_json["error"].append(f'Error [Close order]: {item.get("player_id")} closing order with id: {order.get("data").get("failed")} failed ')
            else:
                # Cancel SL order
                sl_id_list = []
                pending_order = player.get_all_pending(coin_pair)
                for order in pending_order.get("data").get("orders"):
                    if order.get("type") == "STOP" or order.get("type") == "STOP_MARKET":
                        sl_id_list.append(order.get("orderId"))
                order = player.close_order(coin_pair, sl_id_list)
                if order.get("code") != 0 and order.get("code") != 200:
                    ret_json["error"].append(f'Error [Close Order]: {item.get("player_id")} with message: {order.get("msg")}')

                elif order.get("data") and order.get("data").get("failed") != None:
                    ret_json["error"].append(f'Error [Close order]: {item.get("player_id")} closing order with id: {order.get("data").get("failed")} failed')

                # Place new SL
                position = player.get_position(coin_pair)
                if len(position.get("data")) != 0:
                    qty = float(position.get("data")[0].get("positionAmt"))
                    entry = float(position.get("data")[0].get("avgPrice"))
                bingx_dto = dtoBingXOrderTPSL(coin_pair, "sl", buy_sell, result.get("long_short"), entry, qty)
                order_list.append(bingx_dto.to_json())
                order = player.place_order(order_list)
                if order.get("code") != 0 and order.get("code") != 200:
                    ret_json["error"].append(f'Error [Placing SL]: {item.get("player_id")} with message: {order.get("msg")}')
                    continue
                if not ret_json["price"]:
                    ret_json["price"] = player.get_price(coin_pair).get("data").get("price")
        except Exception as e:
            ret_json["error"].append(f'Error [Close order]: {item.get("player_id")} having issue: {e} ')
    return ret_json
