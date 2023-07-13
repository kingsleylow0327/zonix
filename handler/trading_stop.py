from bybit_session import create_session, place_order
from sql_con import ZonixDB

def h_trading_stop(dbcon, player_id, order_dto):
    is_main = True
    # Get related follower
    api_pair_list = dbcon.get_followers_api(player_id)
    # multipier = 1.01 if order_dto.side == "Buy" else 0.99
    if api_pair_list == None or len(api_pair_list) == 0:
        return "StopLoss Shifted (NR)"
    
    origin_side = order_dto.side
    # Shift all stop loss
    for player in api_pair_list:
        session = create_session(player["api_key"], player["api_secret"])
        pos = session.my_position(symbol=order_dto.symbol)["result"]
        stop_px = 0
        for item in pos:
            if item["side"] == origin_side:
                if is_main:
                    stop_px = item["entry_price"]
                    price_decimal = str(stop_px)[::-1].find('.')
                    last_digit = 1
                    for i in range(price_decimal):
                        last_digit = last_digit / 10
                    order_dto.stop_loss = stop_px
                    order_dto.stop_loss = round(order_dto.stop_loss, price_decimal)
                    if order_dto.side == "Buy":
                        order_dto.target_price = order_dto.stop_loss + last_digit
                    else:
                        order_dto.target_price = order_dto.stop_loss - last_digit
                    order_dto.target_price = round(order_dto.target_price, price_decimal)
                    if order_dto.side == "Sell":
                        order_dto.side = "Buy"
                    else:
                        order_dto.side = "Sell"
                    is_main = False
                order_dto.quantity = item["size"]
                break
        if int(order_dto.quantity) == 0:
            continue
        place_order(session,
                    order_dto,
                    market_out=False,
                    is_conditional=True)        
    return "StopLoss Shifted"