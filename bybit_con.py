from logger import Logger
from pybit import usdt_perpetual

# Logger setup
logger_mod = Logger("Place Order")
logger = logger_mod.get_logger()

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

def place_order(session, dtoOrder, is_multple=False):
    force_cross_25(session, dtoOrder.symbol)
    try:
        if not is_multple:
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
                    sl_trigger_by="MarkPrice",
                    position_idx=0,
                )
        else:
            session.place_active_order(
                price=dtoOrder.target_price,
                symbol=dtoOrder.symbol,
                side=dtoOrder.side,
                order_type="Limit",
                qty=dtoOrder.quantity,
                time_in_force="GoodTillCancel",
                reduce_only=False,
                close_on_trigger=False,
                stop_loss=dtoOrder.stop_loss,
                sl_trigger_by="MarkPrice",
                position_idx=0,
            )
    except Exception as e:
        logger.info(e)

def force_cross_25(session, symbol):
    try:
        session.cross_isolated_margin_switch(
        symbol=symbol,
        is_isolated=True,
        buy_leverage=25,
        sell_leverage=25)
    except Exception as e:
        print(e)

    try:
        session.cross_isolated_margin_switch(
        symbol=symbol,
        is_isolated=False,
        buy_leverage=25,
        sell_leverage=25)
    except Exception as e:
        print(e)
