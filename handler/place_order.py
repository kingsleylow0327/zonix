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