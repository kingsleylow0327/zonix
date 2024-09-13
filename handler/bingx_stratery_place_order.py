from bingx.bingx import BINGX
from datetime import datetime
from dto.dto_bingx_order import dtoBingXOrder
from dto.dto_bingx_order_trailing import dtoTrailingOrder
from logger import Logger
from util import convert_percentage_value_to_value as convert_percent
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

def PlaceOrderFunc(player_session, err_array, player_id, order_list, place_order_type):
    # place_order_type - 0: position order, 1: trailing order
    error_label = 'Placing Order' if place_order_type == 0 else 'Placing Trailing Order'
    
    try:
        if place_order_type == 0:
            place_order = player_session.place_order(order_list)
        else:
            place_order = player_session.place_single_order(order_list)

    except Exception as e:
        err_array.append(f'Error [{error_label}]: {player_id} with message: {e}')
        return False

    if place_order == None:
        err_array.append(f'Error [{error_label}]: {player_id} server error')
        return False

    if place_order.get("code") != 0 and place_order.get("code") != 200:
        err_array.append(f'Error [{error_label}]: {player_id} with message: {place_order.get("msg")}')
        return False
    
    return True

def h_bingx_strategy_order(dbcon, order_json, player_id, message_id):
    json_ret            = {"msg": "Order Placed"}
    json_ret["error"]   = []
    
    try:
        strategy            = dbcon.get_strategy_where('name', order_json.get("strategy").lower())
        
        if strategy == None or len(strategy) == 0:
            json_ret["error"].append("Error [Call Strategy]: Strategy was not existed")
            json_ret["status"] = 400
            return json_ret
        
    except Exception as e:
        json_ret["error"].append(f"Error [Call Strategy]: {player_id} with message: {e}")
        return json_ret
    
    api_pair_list       = dbcon.get_strategy_follower(strategy.get("id"), platform, order_type=1)
    
    if api_pair_list == None or len(api_pair_list) == 0:
        json_ret["error"].append("Error [Placing Order]: Not follower following this strategy, actual order execution skipped")
        json_ret["status"] = 400
        return json_ret

    session_list = [{
        "session"       : BINGX(x.get("api_key"), x.get("api_secret")),
        "player_id"     : x.get("follower_id"),
        "damage_cost"   : int(x.get("damage_cost")),
        }for x in api_pair_list
    ]
    
    coin_pair           = order_json.get("coin_pair").strip().replace("/","").replace("-","").upper()
    coin_pair           = coin_pair[:-4] + "-" + coin_pair[-4:]
    current_price       = 0
    stop_loss           = 0
    trailing_stop_price = 0
    is_lower            = order_json.get("order_action") == "SHORT"
    current_time        = datetime.now().strftime('%y%m%d%H%M%S')
    order_link_id       = f"{current_time}-{coin_pair.replace('-', '')}-{str(player_id)[-4:]}"
    record_dto          = None
    
    for player in session_list:
        try:
            wallet = player["session"].get_wallet().get("data").get("balance").get("availableMargin")
        except Exception as e:
            logger.info(f"Error [Placing Strategy]: Wallet issue: {e}")
            json_ret["error"].append(f'Error [Wallet]: {player.get("player_id")} with message: Failed to get Wallet, please check API and Secret')
            continue
        
        if current_price == 0:
            current_price = float(player["session"].get_price(coin_pair).get("data").get("price"))
        if stop_loss == 0:
            stop_loss = convert_percent(current_price, order_json.get("stop_loss"), not is_lower)
        if trailing_stop_price == 0:
            trailing_stop_price = convert_percent(current_price, order_json.get("trailing_stop_price"), is_lower)
        player["session"].order_preset(coin_pair)
        buy_sell = "BUY"
        if order_json.get("order_action") == "SHORT":
            buy_sell = "SELL"
        
        order_list  = []
        rate        = float(order_json.get("trailing_stop_percentage"))
        rate        = rate / 100
        
        if record_dto == None:
            record_dto                  = dtoTrailingOrder(
                coin_pair,   
                buy_sell,
                order_json.get("order_action"),
                None,
                rate,
                trailing_stop_price
            )
            record_dto.player_id        = player_id
            record_dto.message_id       = message_id
            record_dto.order_link_id    = order_link_id
            record_dto.entry            = current_price
            record_dto.stop             = stop_loss
        
        if float(wallet) < minimum_wallet:
            json_ret["error"].append(f'Error [Wallet]: {player.get("player_id")} with message: Wallet Amount is lesser than {minimum_wallet}')
            continue
        qty = calculate_qty(
            wallet,
            float(player["session"].get_price(coin_pair).get("data").get("price")),
            stop_loss,
            float(order_json.get("margin"))
        )
        qty = math.ceil((qty) * 10000) / 10000
        
        # Place Position Order 
        pos_bingx_dto = dtoBingXOrder(
            coin_pair,   
            "MARKET",
            buy_sell,
            order_json.get("order_action"),
            order_json.get("entry_price"),
            qty,
            None,
            None,
            stop_loss,
            qty,
            None
        )
        order_list.append(pos_bingx_dto.to_json())
            
        order_bool = PlaceOrderFunc(player["session"], json_ret["error"], player.get("player_id"), order_list, 0)
        if order_bool is False: continue
        
        # Place Trailing Order
        trailing_bingx_dto = dtoTrailingOrder(
            coin_pair,   
            buy_sell,
            order_json.get("order_action"),
            qty,
            rate,
            trailing_stop_price
        )
            
        order_bool = PlaceOrderFunc(player["session"], json_ret["error"], player.get("player_id"), trailing_bingx_dto.to_json(), 1)  
        if order_bool is False: continue
        
        dbcon.set_order_detail_strategy(record_dto)
            
    return json_ret