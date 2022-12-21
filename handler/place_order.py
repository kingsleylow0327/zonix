from bybit_con import place_order
from dto.dto_order import dtoOrder
from logger import Logger

# Logger setup
logger_mod = Logger("Place Order")
logger = logger_mod.get_logger()

def h_place_order(dbcon, session, message_id):
    result = dbcon.get_order_detail_uat(message_id)
    if result is None:
        logger.info("Empty Row")
        return

    order_detail = dtoOrder(result["entry1"],
        result["coinpair"],
        result["long_short"],
        0.01,
        result["tp1"],
        result["stop"])
    place_order(session, order_detail)
    logger.info("Order Placed")