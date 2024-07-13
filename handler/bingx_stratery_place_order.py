from bingx.bingx import BINGX
from dto.dto_bingx_order import dtoBingXOrder
from logger import Logger
import math
import json

# Logger setup
logger_mod = Logger("Place Order")
logger = logger_mod.get_logger()
maximum_wallet = 3000
minimum_wallet = 300
platform = "bingx"

def calculate_qty(wallet, entry_price, sl, percentage):
    wallet = float(wallet)
    if wallet > maximum_wallet:
        wallet = maximum_wallet
    
    price_diff = entry_price - sl
    if price_diff < 0:
        price_diff *= -1
    
    order_margin = wallet * percentage/100
    qty = order_margin/price_diff 
    return qty


def h_bingx_strategy_order(dbcon, order_json):
    json_ret = {"msg": "Order Placed"}
    json_ret["error"] = []
    
    api_pair_list = dbcon.get_followers_api(order_json.get("strategy"), platform)
    if api_pair_list == None or len(api_pair_list) == 0:
        json_ret["error"].append("Warning [Placing Order]: Both Trader and Follower have not set API, actual order execution skipped")
        return json_ret

    session_list = [{"session":BINGX(x.get("api_key"), x.get("api_secret")),
                     "role": x.get("role"),
                     "player_id": x.get("follower_id"),
                     "damage_cost": int(x.get("damage_cost"))} for x in api_pair_list]
    
    coin_pair = order_json.get("coin_pair").strip().replace("/","").replace("-","").upper()
    coin_pair = coin_pair[:-4] + "-" + coin_pair[-4:]
    
    for player in session_list:
        try:
            wallet = player["session"].get_wallet().get("data").get("balance").get("availableMargin")
        except:
            json_ret["error"].append(f'Error [Wallet]: {player.get("player_id")} with message: Failed to get Wallet, please check API and Secret')
            continue
        if float(wallet) < minimum_wallet:
            json_ret["error"].append(f'Error [Wallet]: {player.get("player_id")} with message: Wallet Amount is lesser than {minimum_wallet}')
            continue
        player["session"].order_preset(coin_pair)
        buy_sell = "BUY"
        if order_json.get("order_action") == "SHORT":
            buy_sell = "SELL"
        order_list = []
        qty = calculate_qty(wallet,
                            order_json.get("entry_price"),
                            order_json.get("stop_lost"),
                            float(order_json.get("margin")))
        qty = math.ceil((qty) * 10000) / 10000
        bingx_dto = dtoBingXOrder(coin_pair,   
                                  "LIMIT",
                                  buy_sell,
                                  order_json.get("order_action"),
                                  order_json.get("entry_price"),
                                  qty,
                                  order_json.get("take_profit"),
                                  qty,
                                  order_json.get("stop_loss"),
                                  qty
                                  )
        order_list.append(bingx_dto.to_json())
        try:
            order = player["session"].place_order(order_list)
        except Exception as e:
            json_ret["error"].append(f'Error [Placing Order]: {player.get("player_id")} with message: {e}')
            continue

        if order == None:
            json_ret["error"].append(f'Error [Placing Order]: {player.get("player_id")} server error')
            continue

        if order.get("code") != 0 and order.get("code") != 200:
            json_ret["error"].append(f'Error [Placing Order]: {player.get("player_id")} with message: {order.get("msg")}')
            continue

    return json_ret