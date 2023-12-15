from bybit_session import create_session, cancel_order, cancel_all_order, cancel_pos, get_coin_info, order_preset, place_order
from dto.dto_order import dtoOrder
from logger import Logger

# Logger setup
logger_mod = Logger("Cancel Order")
logger = logger_mod.get_logger()
platform = "bybit"

def h_cancel_all(dbcon, coin, is_active):
    player_api_list = dbcon.get_all_player()
    for i in player_api_list:
        session = create_session(i["api_key"], i["api_secret"])
        cancel_all_order(session, coin, is_active)
    return "Cancel All Done"

def h_cancel_order(dbcon, order_detail, is_not_tp=True):
    result = order_detail
    if result is None:
        return "Empty Row"
    
    # get api list
    api_pair_list = dbcon.get_followers_api(result["player_id"], platform)
    if api_pair_list == None or len(api_pair_list) == 0:
        return "Order Placed (NR)"

    session_list = [{"session":create_session(x["api_key"], x["api_secret"]),
        "role": x["role"], "player_id": x["follower_id"]} for x in api_pair_list]
    
    # Coin Pair and Refer ID
    coin_pair = result["coinpair"].strip().replace("/","").upper()
    order_refer_id = result["order_link_id"]

    for item in session_list:
        session = item["session"]
        # Market Out
        if is_not_tp:
            cancel_pos(session, coin_pair)
            # Cancel Condition
            session.cancel_all_conditional_orders(symbol=coin_pair)

        # Cancel Active order
        for i in range(1, 9):
            refer_id = f'{order_refer_id}-{str(i)}'
            cancel_order(session, coin_pair, refer_id)

    return "Order Cancelled"
