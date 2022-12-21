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
    
    result["qty"] = calculate_qty(session, result["entry1"])
    order_detail = dtoOrder(result["entry1"],
        result["coinpair"],
        result["long_short"],
        result["qty"],
        result["tp1"],
        result["stop"])
    place_order(session, order_detail)
    # follow_order(order_detail)
    return "Order Placed"

def follow_order(order_detail):
    # DB get API Key and APi Secret


    # Follower Session
    session = create_session("", "")

    # Calculate Follower quantity
    order_detail.quantity = calculate_qty(session, order_detail.target_price)
    place_order(session, order_detail)

def calculate_qty(session, entry_price, percentage = 2):
    wallet = session.get_wallet_balance(coin="USDT")["result"]["USDT"]["equity"]
    qty = (wallet * (percentage / 100) * 25)/entry_price
    return "{:.3}".format(qty)