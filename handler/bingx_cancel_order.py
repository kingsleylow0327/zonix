from bingx.bingx import BINGX
from logger import Logger
from dto.dto_bingx_order import dtoBingXOrder

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

def h_bingx_cancel_order(dbcon, order_detail, is_not_tp=True):
    result = order_detail
    if result is None:
        return "Empty Row"
    
    # get api list
    api_pair_list = dbcon.get_followers_api(result["player_id"], platform)
    if api_pair_list == None or len(api_pair_list) == 0:
        return "Order Placed (NR)"

    session_list = [{"session":BINGX(x["api_key"], x["api_secret"]),
        "role": x["role"], "player_id": x["follower_id"]} for x in api_pair_list]
    
    # Coin Pair and Refer ID
    coin_pair = result["coinpair"].strip().replace("/","").replace("-","").upper()
    coin_pair = coin_pair[:-4] + "-" + coin_pair[-4:]
    # order_refer_id = result["order_link_id"]
    ret_json = {}
    ret_json["status"] = "Order Cancelled"
    for item in session_list:
        player = item["session"]
        # Market Out
        if is_not_tp:
            position = player.get_position(coin_pair)
            buy_sell = "BUY"
            if result["long_short"] == "LONG":
                buy_sell = "SELL"
            if len(position.get("data")) != 0:
                qty = float(position.get("data")[0].get("positionAmt"))
                bingx_dto = dtoBingXOrder(coin_pair, "MARKET", buy_sell, result.get("long_short"), None , qty, None, None, None, None, None)
                order_list = []
                order_list.append(bingx_dto.to_json())
                order = player.place_order(order_list)
                current_price = player.get_price(coin_pair)
                if ret_json.get("price") == None: 
                    ret_json["price"] = current_price
            # Cancel Condition
            # session.cancel_all_conditional_orders(symbol=coin_pair)

        # Cancel Active order
        player.close_all_order(coin_pair)

    return ret_json
