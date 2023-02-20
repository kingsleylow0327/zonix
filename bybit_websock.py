from bybit_session import *
from dto.dto_order import dtoOrder
from logger import Logger
from pybit import usdt_perpetual
from config import Config
import json

# Logger setup
logger_mod = Logger("Websocket")
logger = logger_mod.get_logger()
CONFIG = Config()

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
            test=eval(CONFIG.IS_TEST),
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
        # print("-----------------Order Stream--------------------")
        # print(json.dumps(message, indent=2))
        # print("\n")

        data = message["data"]
        coin = data[0]["symbol"]

        # Check if it's taking profit
        for item in data:
            if item["create_type"] == "CreateByPartialTakeProfit":
                data = item
                # print(" CreateByPartialTakeProfit ")
                break
            # print(" Not Take Profit ")
            return
        session = create_session(self.api_key, self.api_secret)
        my_pos = session.my_position(symbol=coin)["result"]

        qty = 0
        stop_px = 0
        qty_decimal = 0
        # Compare my_pos side with Data
        for item in my_pos:
            if item["side"] != data["side"]:
                stop_px = item["entry_price"]
        
        # Cancel active order and conditional order
        session.cancel_all_active_orders(symbol=coin)
        condi = session.get_conditional_order(symbol=coin)
        for item in condi["result"]["data"]:
            if item["order_status"] != "Untriggered":
                continue
            qty_decimal = str(item["qty"])[::-1].find('.')
            if item["trigger_by"] == "MarkPrice":
                qty += item["qty"]
            if item["close_on_trigger"] == False:
                session.cancel_conditional_order(
                    symbol=coin,
                    stop_order_id=item["stop_order_id"])

        # Place Conditional
        price_decimal = str(stop_px)[::-1].find('.')
        base_price = stop_px * (1.03 if data["side"] == "Sell" else 0.97) # Might need match decimal format
        base_price = round(base_price, price_decimal)
        qty = round(qty, qty_decimal)
        order_detail = dtoOrder(base_price,
                            data["symbol"],
                            data["side"],
                            qty,
                            0,
                            stop_px,
                            0)
        place_order(session, order_detail, is_conditional=True)


    def handle_execution(message):
        print("-----------------Execution Stream--------------------")
        print(json.dumps(message, indent=2))
        print("\n")    