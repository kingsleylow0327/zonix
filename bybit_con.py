import os
from dotenv import load_dotenv

import time
from dto.dto_order import dtoOrder
from time import sleep
from pybit import usdt_perpetual

load_dotenv()
BYBIT_API_KEY = os.getenv('BYBIT_API_KEY')
BYBIT_API_SECRET = os.getenv('BYBIT_API_SECRET')

# Initialize web socket connection instance
def create_web_socket(api_key, api_secret):    
    ws = usdt_perpetual.WebSocket(
        test=True,
        api_key=api_key,
        api_secret=api_secret)
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
    print(message)
    print("\n")

def handle_order(message):
    print("-----------------Order Stream--------------------")
    print(message)
    print("\n")


def handle_execution(message):
    print("-----------------Execution Stream--------------------")
    print(message)
    print("\n")

def place_order(session, dtoOrder):
    session.place_active_order(
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
            sl_trigger_by="LastPrice",
            position_idx=0,
        )

if "__main__" == __name__:
    target_price = 16660

    order_detail = dtoOrder(
        target_price,
        "BTCUSDT",
        "Buy",
        0.01,
        target_price + (target_price * 0.05),
        target_price - (target_price * 0.05))
    
    session = create_session(BYBIT_API_KEY, BYBIT_API_SECRET)
    ws = create_web_socket(BYBIT_API_KEY, BYBIT_API_SECRET)
    ws.order_stream(callback=handle_order)
    ws.execution_stream(callback=handle_execution)
    #ws.position_stream(callback=handle_position)

    try:
        place_order(session, order_detail)
    except Exception as e:
        print("Failed to place oreder")
        print("Error: " + str(e))

    while True:
        time.sleep(1)
