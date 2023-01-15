from dto.dto_order import dtoOrder
from logger import Logger
from pybit import usdt_perpetual
import json
import requests
import time

# Logger setup
logger_mod = Logger("Place Order")
logger = logger_mod.get_logger()
GLOBALDB = None

def get_coin_info(coin):
    r = requests.get("https://api-testnet.bybit.com/derivatives/v3/public/instruments-info?category=linear&symbol={}".format(coin))
    result = json.loads(r.text)
    return {"qtyStep":result["result"]["list"][0]["lotSizeFilter"]["qtyStep"],
    "minOrderQty":result["result"]["list"][0]["lotSizeFilter"]["minOrderQty"],
    "maxLeverage":result["result"]["list"][0]["leverageFilter"]["maxLeverage"]}

# Initialize web socket connection instance
def create_web_socket(api_key, api_secret):
    # global GLOBALDB
    # GLOBALDB = dbcon   
    ws = usdt_perpetual.WebSocket(
        test=True,
        api_key=api_key,
        api_secret=api_secret)
    # ws.execution_stream(handle_execution)
    # ws.position_stream(handle_position)
    ws.order_stream(handle_order)
    return ws

# Initialize http connection instance
def create_session(api_key, api_secret):
    session = usdt_perpetual.HTTP(endpoint="https://api-testnet.bybit.com",
        api_key=api_key,
        api_secret=api_secret)
    return session

# handle_position is a callback that will be triggered on every new websocket event (push frequency can be 1-60s)
def handle_position(message):
    print("-----------------Pos Stream--------------------")
    print(json.dumps(message, indent=2))
    print("\n")

def handle_order(message):
    print("-----------------Order Stream--------------------")
    print(json.dumps(message, indent=2))
    print("\n")
    data = json.loads(message)["data"]
    if data != "CreateByPartialTakeProfit":
        return
    
    # Create Session
    session = create_session(api_key, api_secret)
    # Check if session have active order:
    

    # Cancel active order

    # Place Conditional
    price_decimal = '.{}f'.format(str(data["price"])[::-1].find('.'))
    base_price = data["price"] * (1.03 if data["side"] == "Sell" else 0.97) # Might need match decimal format
    base_price = price_decimal.format(str(base_price))
    order_detail = dtoOrder(base_price,
                        data["symbol"],
                        data["side"],
                        data["qty"] * 4,
                        data["price"],
                        0,
                        0)
    place_order(session, order_detail, is_conditional=True)


def handle_execution(message):
    print("-----------------Execution Stream--------------------")
    print(json.dumps(message, indent=2))
    print("\n")

def place_order(session, dtoOrder, market_out=False, is_conditional=False):
    ret = None
    try:
        if is_conditional:
            ret = session.place_conditional_order(
                symbol=dtoOrder.symbol,
                order_type="Market",
                side=dtoOrder.side,
                qty=dtoOrder.quantity,
                base_price=dtoOrder.target_price, # 0.97 if Buy Entry Price from WS
                stop_px=dtoOrder.stop_loss,  # Change to Entry Price from WS
                time_in_force="GoodTillCancel",
                trigger_by="MarkPrice",
                reduce_only=True,
                close_on_trigger=False
            )
        elif not market_out:
            ret = session.place_active_order(
                    price=dtoOrder.target_price,
                    symbol=dtoOrder.symbol,
                    side=dtoOrder.side,
                    order_type="Limit",
                    qty=dtoOrder.quantity,
                    time_in_force="GoodTillCancel",
                    reduce_only=False,
                    close_on_trigger=False,
                    take_profit=dtoOrder.take_profit,
                    tp_trigger_by="LastPrice",
                    stop_loss=dtoOrder.stop_loss,
                    sl_trigger_by="MarkPrice",
                )
        else:
            fliped_side = flip_side(dtoOrder.side)
            ret = session.place_active_order(
                symbol=dtoOrder.symbol,
                side=fliped_side,
                order_type="Market",
                qty=dtoOrder.quantity,
                time_in_force="ImmediateOrCancel",
                reduce_only=True,
                close_on_trigger=False, 
            )
        return ret
    except Exception as e:
        logger.warning(e)
        return "error"

def cancel_pos(session, coin):
    return session.close_position(coin)

def cancel_order(session, coin, order_id):
    try:
        ret = session.cancel_active_order(
                symbol=coin,
                order_id=order_id,
                type="TpSlConditional")
        return ret
    except Exception as e:
        logger.warning(e)
        return "error"

def flip_side(side):
    ret = side
    if side == "Buy":
        ret = "Sell"
    else:
        ret = "Buy"
    return ret

def order_preset(session, symbol, lev):
    my_pos = session.my_position(symbol=symbol)["result"][0]
    # Set TP SL
    if my_pos["tp_sl_mode"] == "Full":
        session.full_partial_position_tp_sl_switch(
            symbol=symbol,
            tp_sl_mode="Partial"
        )
    
    # Set Position Mode
    if my_pos["mode"] != "BothSide":
        session.position_mode_switch(
            symbol=symbol,
            mode="BothSide"
        )
    
    # Set Corss and Leverage
    if my_pos["is_isolated"] != False or my_pos["leverage"] != lev:
        try:
            session.cross_isolated_margin_switch(
            symbol=symbol,
            is_isolated=True,
            buy_leverage=lev,
            sell_leverage=lev)
        except Exception as e:
            logger.warning(e)

        try:
            session.cross_isolated_margin_switch(
            symbol=symbol,
            is_isolated=False,
            buy_leverage=lev,
            sell_leverage=lev)
        except Exception as e:
            logger.warning(e)
