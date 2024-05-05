import traceback
from bingx.bingx import BINGX
from logger import Logger
from dto.dto_bingx_order import dtoBingXOrder

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
    for item in session_list:
        player = item["session"]
        # Market Out half
        buy_sell = "BUY"
        if result["long_short"] == "LONG":
            buy_sell = "SELL"
        try:
            # Get current coin's amount
            amt = 0
            pos_ret = player.get_position(coin_pair)
            # If error, skip
            if pos_ret.get("code") != 0:
                ret_json["error"].append(f'Error [PTP]: {item.get("player_id")} having issue: {pos_ret.get("msg")} ')
                continue
            position_list = pos_ret.get("data")
            for position in position_list:
                if position.get("positionSide") == "SHORT":
                    amt = float(position.get("positionAmt"))
            if amt == 0:
                continue
            # TP half (place order)
            bingx_dto = dtoBingXOrder(coin_pair,
                                "MARKET",
                                buy_sell,
                                result["long_short"],
                                0,
                                amt/2,
                                0,
                                0,
                                0,
                                0)
            order = player.place_order([bingx_dto.to_json()])
            if order.get("code") != 0:
                ret_json["error"].append(f'Error [PTP]: {item.get("player_id")} having issue: {order.get("msg")} ')
        except Exception as e:
            try:
                logger.error(traceback.format_exc())
            except Exception as e:
                pass
            ret_json["error"].append(f'Error [PTP]: {item.get("player_id")} having issue: {e} ')
    return ret_json
