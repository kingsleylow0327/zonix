from bybit_session import *
from dto.dto_order import dtoOrder
from logger import Logger
from pybit import usdt_perpetual
import json
import time

# Logger setup
logger_mod = Logger("Websocket")
logger = logger_mod.get_logger()

MAX_TAKE_PROFIT = 4

class bybit_ws():
    def __init__(self, api_key, api_secret) -> None:
        self.api_key = api_key
        self.api_secret = api_secret
        self.websocket = self.create_web_socket(api_key, api_secret)

    # Initialize web socket connection instance
    def create_web_socket(self, api_key, api_secret):
        # global GLOBALDB
        # GLOBALDB = dbcon   
        ws = usdt_perpetual.WebSocket(
            test=True,
            api_key=api_key,
            api_secret=api_secret)
        # ws.execution_stream(handle_execution)
        ws.order_stream(self.handle_order)
        return ws

    # handle_position is a callback that will be triggered on every new websocket event (push frequency can be 1-60s)
    def handle_position(message):
        print("-----------------Pos Stream--------------------")
        print(json.dumps(message, indent=2))
        print("\n")
    
    def handle_order(self, message):
        print("-----------------Order Stream--------------------")
        print(json.dumps(message, indent=2))
        print("\n")

        data = message["data"]
        coin = data[0]["symbol"]

        # Check if it's taking profit
        for item in data:
            if item["create_type"] == "CreateByPartialTakeProfit":
                data = item
                print(" CreateByPartialTakeProfit ")
                break
            print(" Not Take Profit ")
            return
        session = create_session(self.api_key, self.api_secret)
        my_pos = session.my_position(symbol=coin)["result"]

        qty = 0
        stop_px = 0
        # Compare my_pos side with Data
        for item in my_pos:
            if item["side"] != data["side"]:
                stop_px = item["entry_price"]
                qty = item["size"]

        # # Check if session have active order with same side:
        # session_result = session.get_active_order(symbol=coin)["result"]["data"]
        # total_qty = 0

        # print("---------------------------")
        # for item in session_result:
        #     if item["order_status"] == "New":
        #         total_qty += item["qty"]
        #         print(json.dumps(item, indent=2))
        
        # Cancel active order
        session.cancel_all_active_orders(symbol=coin)
        session.cancel_all_conditional_orders(symbol=coin)

        # Place Conditional
        price_decimal = str(stop_px)[::-1].find('.')
        base_price = stop_px * (1.03 if data["side"] == "Sell" else 0.97) # Might need match decimal format
        base_price = round(base_price, price_decimal)
        order_detail = dtoOrder(base_price,
                            data["symbol"],
                            data["side"],
                            qty * MAX_TAKE_PROFIT,
                            0,
                            stop_px,
                            0)
        place_order(session, order_detail, is_conditional=True)


    def handle_execution(message):
        print("-----------------Execution Stream--------------------")
        print(json.dumps(message, indent=2))
        print("\n")    