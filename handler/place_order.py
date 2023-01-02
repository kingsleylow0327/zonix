import decimal
from bybit_con import  create_session, place_order, create_web_socket, get_coin_info
from dto.dto_order import dtoOrder
from logger import Logger

# Logger setup
logger_mod = Logger("Place Order")
logger = logger_mod.get_logger()

def calculate_qty(session, entry_price, coin_info, percentage = 2):
    wallet = session.get_wallet_balance(coin="USDT")["result"]["USDT"]["equity"]
    qty = (wallet * (percentage / 100) * float(coin_info["maxLeverage"]))/entry_price
    
    # Make it same decimal place
    decimal_place = decimal.Decimal(coin_info["qtyStep"]).as_tuple().exponent * -1
    return format(qty, '.{}f'.format(str(decimal_place)))

def h_place_order(dbcon, message_id):
    result = dbcon.get_order_detail_uat(message_id)
    if result is None:
        return "Empty Row"
    
    # get api list
    api_pair_list = dbcon.get_followers_api(result["player_id"])
    session_list = [{"session":create_session(x["api_key"], x["api_secret"])} for x in api_pair_list]

    # Count number of Entry Point
    entry_list = [x for x in [result["entry1"], result["entry2"]] if x != -1.0]
    entry_count = len(entry_list)

    # Count number of take profit
    tp_list = [x for x in [result["tp1"], result["tp2"], result["tp3"], result["tp4"]] if x != -1.0]
    tp_num = len(tp_list)

    # Get Coin Info
    coin_info = get_coin_info(result["coinpair"].strip().replace("/","").upper())
    coin_qty_step = str(decimal.Decimal(coin_info["qtyStep"]).as_tuple().exponent * -1)
            
    for item in session_list:        
        for e in range(entry_count): 
            total_qty = float(calculate_qty(item["session"], entry_list[0], coin_info, percentage = 2))
            # Entry
            single_current_qty = float(format(total_qty/entry_count/tp_num, '.{}f'.format(str(coin_qty_step))))
            exceeding_qty = total_qty/entry_count - (single_current_qty*tp_num) + single_current_qty
            exceeding_qty = float(format(exceeding_qty, '.{}f'.format(str(coin_qty_step))))
            for i in range(tp_num):
                if i == tp_num -1:
                    single_current_qty = exceeding_qty
                order_detail = dtoOrder(entry_list[e],
                        result["coinpair"],
                        result["long_short"],
                        single_current_qty,
                        tp_list[i],
                        result["stop"],
                        coin_info["maxLeverage"])
                place_order(item["session"], order_detail)

    return "Order Placed" 