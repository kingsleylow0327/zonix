import decimal
from bybit_session import create_session, place_order, get_coin_info, order_preset
from dto.dto_order import dtoOrder
from logger import Logger
import tapbit.swap_api as tapbit
import tapbit.utils as tutils

# Logger setup
logger_mod = Logger("Place Order")
logger = logger_mod.get_logger()
order_percent = 5
maximum_wallet = 3000

def calculate_qty(session, entry_price, coin_info, percentage = 2):
    wallet = session.get_wallet_balance(coin="USDT")["result"]["USDT"]["equity"]
    if float(wallet) > maximum_wallet:
        wallet = maximum_wallet
    qty = (wallet * (percentage / 100) * float(coin_info["maxLeverage"]))/entry_price
    
    # Make it same decimal place
    decimal_place = decimal.Decimal(coin_info["qtyStep"]).as_tuple().exponent * -1
    return format(qty, '.{}f'.format(str(decimal_place)))

def h_place_order(dbcon, message_id):
    result = dbcon.get_order_detail_by_order(message_id)
    if result is None:
        return "Empty Row"
    
    # get api list
    api_pair_list = dbcon.get_followers_api(result["player_id"])
    if api_pair_list == None or len(api_pair_list) == 0:
        return "Order Placed (NR)"

    session_list = [{"session":create_session(x["api_key"], x["api_secret"]),
        "role": x["role"], "player_id": x["follower_id"]} for x in api_pair_list]

    # Count number of Entry Point
    entry_list = [x for x in [result["entry1"], result["entry2"]] if x != -1.0]
    entry_count = len(entry_list)

    # Count number of take profit
    tp_list = [x for x in [result["tp1"], result["tp2"], result["tp3"], result["tp4"]] if x != -1.0]
    tp_num = len(tp_list)

    # Get Coin Info
    coin_pair = result["coinpair"].strip().replace("/","").upper()
    coin_info = get_coin_info(coin_pair)
    coin_qty_step = str(decimal.Decimal(coin_info["qtyStep"]).as_tuple().exponent * -1)

    # get refer id
    order_refer_id = result["order_link_id"]
    
    p_order_id_list = []
    order_id_map = {}

    for item in session_list:
        is_player = item["role"] == "player"
        sub_order_id_list = []
        order_preset(item["session"], coin_pair, coin_info["maxLeverage"])
        counter = 1
        for e in range(entry_count):
            total_qty = float(calculate_qty(item["session"], entry_list[0], coin_info, percentage = order_percent))
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
                order_detail.order_link_id = f'{order_refer_id}-{str(counter)}'
                counter += 1
                order = place_order(item["session"], order_detail)
                if order == "error":
                    logger.warning(item["player_id"])
                    continue
                if is_player:
                    p_order_id_list.append(order["result"]["order_id"])
                sub_order_id_list.append(
                    {"id":order["result"]["order_id"],
                    "qty":single_current_qty})
        order_id_map[item["player_id"]]=sub_order_id_list

    # Save into db, using message_id and list of order id
    dbcon.set_message_player_order(message_id, p_order_id_list)
    dbcon.set_player_follower_order(order_id_map, result["player_id"])

    return "Order Placed"

def h_tapbit_place_order(order, dbcon, alpha):
    api_pair_list = dbcon.get_followers_api(alpha)
    if api_pair_list == None or len(api_pair_list) == 0:
        return "Alpha Error"

    session_list = [{"session":tapbit.SwapAPI(x["api_key"], x["api_secret"]),
        "role": x["role"], "player_id": x["follower_id"]} for x in api_pair_list]

    coin_pair = order["coinpair"].strip().split("/")[0]
    coin_info = tutils.check_coin(coin_pair)
    if coin_info == None:
        logger.warning(f"{coin_pair} not found")
        return "Coin Error"
    max_lev = float(coin_info["max_leverage"])
    multiplier = float(coin_info["multiplier"])

    coin_qty_step = (max_lev/float(order["entry1"])) / multiplier
    for item in session_list:
        # if is_tpsl:
        #     position = item["session"].get_position(coin_pair)["data"]
        #     quantity = '0'
        #     for pos in position:
        #         if pos["side"].upper() == result['long_short'] and pos["quantity"] != "0":
        #             quantity = pos["quantity"]
        #             break
        #     if quantity == '0':
        #         logger.warning(f'{item["player_id"]} TPSL not placed due to no position')
        #         continue
        #     direction = 'closeShort' if result['long_short'] == 'SHORT' else 'closeLong'
        #     item["session"].place_tpsl(coin_pair, str(result['tp1']), result['stop'], quantity, direction)
        if True:
            wallet = float(item["session"].get_accounts()["data"]["available_balance"])
            min_order = 2
            if wallet * (order_percent/100) > 2:
                min_order = wallet * (order_percent/100)

            direction = 'openShort' if order['long_short'] == 'SELL' else 'openLong'
            qty = min_order * coin_qty_step
            item["session"].order(coin_pair, 'crossed', direction, str(int(qty)), str(int(order["entry1"])), str(int(max_lev)), 'limit')
    return "Order Placed"

def h_tapbit_cancel_order(author, dbcon, coin_pair, side=None):
    side=side.upper()
    coin_pair = coin_pair.upper()
    api_pair_list = dbcon.get_followers_api(author)
    if api_pair_list == None or len(api_pair_list) == 0:
        return "Order Placed (NR)"

    session_list = [{"session":tapbit.SwapAPI(x["api_key"], x["api_secret"]),
        "role": x["role"], "player_id": x["follower_id"]} for x in api_pair_list]
    
    for item in session_list:
        position = item["session"].get_position(coin_pair)["data"]
        quantity = '0'
        if len(position) != 0:
            for pos in position:
                if pos["side"].upper() == side and pos["quantity"] != "0":
                    quantity = pos["quantity"]
                    break
            if quantity == '0':
                logger.warning(f'{item["player_id"]} TPSL not placed due to no position')
                continue

            direction = 'closeShort' if side == 'SHORT' else 'closeLong'
            item["session"].order(coin_pair, 
                              'crossed', 
                              direction, 
                              str(int(quantity)), 
                              str(int(float(pos["mark_price"]))), 
                              str(pos['leverage']), 
                              'market')

        order_list = item["session"].get_order_list(coin_pair)["data"]
        if len(order_list) != 0:
            for order in order_list:
                if coin_pair in order["contract_code"] and side in order["direction"].upper():
                    item["session"].cancel(order["order_id"])

        return "Order canceled"
