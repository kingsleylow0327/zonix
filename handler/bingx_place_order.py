from bingx.bingx import BINGX
from dto.dto_bingx_order import dtoBingXOrder
from logger import Logger

# Logger setup
logger_mod = Logger("Place Order")
logger = logger_mod.get_logger()
order_percent = 3
maximum_wallet = 1000
platform = "bingx"

def calculate_qty(wallet, entry_price, sl, ratio, percentage = 2):
    if float(wallet) > maximum_wallet:
        wallet = maximum_wallet
    
    price_diff = entry_price - sl
    if price_diff < 0:
        price_diff *= -1
    
    order_margin = wallet * ratio * percentage/100
    qty = order_margin/price_diff 
    return round(qty, 3)


def h_bingx_order(dbcon, message_id):
    result = dbcon.get_order_detail_by_order(message_id)
    if result is None:
        return "Empty Row"
    
    # get api list
    api_pair_list = dbcon.get_followers_api(result["player_id"], platform)
    if api_pair_list == None or len(api_pair_list) == 0:
        return "Order Placed (NR)"

    session_list = [{"session":BINGX(x["api_key"], x["api_secret"]),
        "role": x["role"], "player_id": x["follower_id"]} for x in api_pair_list]

    # Count number of Entry Point
    entry_list = [x for x in [result["entry1"], result["entry2"]] if x != -1.0]
    entry_count = len(entry_list)

    # Count number of take profit
    tp_list = [x for x in [result["tp1"], result["tp2"], result["tp3"], result["tp4"]] if x != -1.0]
    tp_num = len(tp_list)

    # Get Coin Info
    coin_pair = result["coinpair"].strip().replace("/","").replace("-","").upper()
    coin_pair = coin_pair[:-4] + "-" + coin_pair[-4:]

    # Stoploss
    stop_loss = result["stop"]

    # get refer id
    order_refer_id = result["order_link_id"]
    
    p_order_id_list = []
    order_id_map = {}

    for player in session_list:
        is_player = player["role"] == "player"
        order_list = []
        sub_order_id_list = []
        player["session"].order_preset(coin_pair)
        counter = 1
        wallet = player["session"].get_wallet()
        ratio = 100 / (tp_num * entry_count) / 100
        buy_sell = "BUY"
        if result["long_short"] == "SHORT":
            buy_sell = "SELL"
        for entry in entry_list:
            for tp in tp_list:
                order_link_id = f'{order_refer_id}-{str(counter)}'
                qty = calculate_qty(wallet, entry, tp, ratio)
                bingx_dto = dtoBingXOrder(coin_pair,
                                             "LIMIT",
                                             buy_sell,
                                             result["long_short"],
                                             entry,
                                             qty,
                                             tp,
                                             qty,
                                             stop_loss,
                                             qty,
                                             order_link_id
                                             )
                counter += 1
                order_list.append(bingx_dto.to_json())
                if is_player:
                    p_order_id_list.append(order_link_id)
                # sub_order_id_list.append(
                #     {"id":order_link_id,
                #     "qty":qty})
        order = player["session"].place_order(order_list)
        if order.get("code") != 0 and order.get("code") != 200:
            return order.get("msg")
        order_id_map[player["player_id"]]=sub_order_id_list
    dbcon.set_message_player_order(message_id, p_order_id_list)
    # dbcon.set_player_follower_order(order_id_map, result["player_id"])
    return "Order Placed" 