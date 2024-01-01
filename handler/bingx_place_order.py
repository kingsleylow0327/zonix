from bingx.bingx import BINGX
from dto.dto_bingx_order import dtoBingXOrder
from logger import Logger
import math
import json

# Logger setup
logger_mod = Logger("Place Order")
logger = logger_mod.get_logger()
order_percent = 3
maximum_wallet = 1000
platform = "bingx"

def calculate_qty(wallet, entry_price, sl, percentage = 2):
    if float(wallet) > maximum_wallet:
        wallet = maximum_wallet
    
    price_diff = entry_price - sl
    if price_diff < 0:
        price_diff *= -1
    
    order_margin = wallet * percentage/100
    qty = order_margin/price_diff 
    return qty


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
    entry_list = [float(x) for x in [result["entry1"], result["entry2"]] if x != -1.0]
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
    
    order_id_map = []

    error_ret = ""

    json_ret = {"msg": "Order Placed"}

    for player in session_list:
        order_list = []
        try:
            wallet = player["session"].get_wallet().get("data").get("balance").get("availableMargin")
        except:
            error_ret += f'Error [Wallet]: {player.get("player_id")} with message: Failed to get Wallet, please check API and Secret \n'
            continue
        player["session"].order_preset(coin_pair)
        counter = 1
        buy_sell = "BUY"
        if result["long_short"] == "SHORT":
            buy_sell = "SELL"
        average_entry = sum(entry_list)/entry_count
        for entry in entry_list:
            for tp in tp_list:
                # 3 decimal place
                qty = calculate_qty(wallet, average_entry, stop_loss) / entry_count / tp_num
                qty = math.ceil((qty) * 1000) / 1000
                order_link_id = f'{order_refer_id}-{str(counter)}'
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
        order = player["session"].place_order(order_list)
        if order.get("code") != 0 and order.get("code") != 200:
            error_ret += f'Error [Placing Order]: {player.get("player_id")} with message: {order.get("msg")} \n'
            continue

        for item in order["data"]["orders"]:
            order_detail_pair = {"player_id" : player.get("player_id"),
                                "client_order_id" : item.get("clientOrderID"),
                                "order_id" : item.get("orderId")}
            order_id_map.append(order_detail_pair)
    dbcon.set_client_order_id(order_id_map, message_id)
    if error_ret != "":
        json_ret["error"] = f"MsgId - {message_id} having following Error: \n" + error_ret
    return json_ret