from bybit_con import  create_session, place_order
from dto.dto_order import dtoOrder
from logger import Logger

# Logger setup
logger_mod = Logger("Place Order")
logger = logger_mod.get_logger()

def h_place_order(dbcon, session, message_id):
    result = dbcon.get_order_detail_uat(message_id)
    if result is None:
        return "Empty Row"
    
    api_pair_list = dbcon.get_followers_api(result["player_id"])
    for item in api_pair_list:
        try:
            session = create_session(item["api_key"], item["api_secret"])
            result["qty"] = calculate_qty(session, result["entry1"])
            order_detail = dtoOrder(result["entry1"],
                result["coinpair"],
                result["long_short"],
                result["qty"],
                result["tp1"],
                result["stop"])
            place_order(session, order_detail)
        except Exception as e:
            logger.info("Follower {} not able to place order".format(item["follower_id"]))
            logger.info(e)

    return "Order Placed"

def calculate_qty(session, entry_price, percentage = 2):
    wallet = session.get_wallet_balance(coin="USDT")["result"]["USDT"]["equity"]
    qty = (wallet * (percentage / 100) * 25)/entry_price
    return "{:.3}".format(qty)

def h_place_order_test(dbcon, message_id):
    result = dbcon.get_order_detail_uat(message_id)
    if result is None:
        return "Empty Row"
    
    # get api list
    api_pair_list = dbcon.get_followers_api(result["player_id"])
    session_list = [create_session(x["api_key"], x["api_secret"]) for x in api_pair_list]

    # Entry Point List
    entry_list = [result["entry1"], result["entry2"]]

    # Count number of take profit
    tp_list = [x for x in [result["tp1"], result["tp2"], result["tp3"], result["tp4"]] if x != -1.0]
    tp_num = len(tp_list)
    
    for session in session_list:
        if result["entry2"] == -1.0:
            total_qty = float(calculate_qty(session, entry_list[0], percentage = 2))
            for i in range(tp_num):
                order_detail = dtoOrder(entry_list[0],
                    result["coinpair"],
                    result["long_short"],
                    total_qty/tp_num,
                    tp_list[i],
                    result["stop"])
                place_order(session, order_detail)
        else:
            for i in range(2):
                total_qty = float(calculate_qty(session, entry_list[i], percentage = 2))
                order_detail = dtoOrder(entry_list[i],
                    result["coinpair"],
                    result["long_short"],
                    total_qty/2,
                    0,
                    result["stop"])
                place_order(session, order_detail, is_multple=True)      
