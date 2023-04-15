from bybit_session import create_session, place_order
from sql_con import ZonixDB

def h_trading_stop(dbcon, player_id, order_dto):
    # Get related follower
    api_pair_list = dbcon.get_followers_api(player_id)
    multipier = 1.01 if order_dto.side == "Buy" else 0.99
    order_dto.target_price = order_dto.target_price * multipier
    if api_pair_list == None or len(api_pair_list) == 0:
        return "StopLoss Shifted (NR)"
    
    # Shift all stop loss
    for player in api_pair_list:
        session = create_session(player["api_key"], player["api_secret"])
        pos = session.my_position(symbol=order_dto.symbol)["result"]
        stop_px = 0
        for item in pos:
            if item["side"] == order_dto.side:
                stop_px = item["entry_price"]
                price_decimal = str(stop_px)[::-1].find('.')
                order_dto.target_price = round(order_dto.target_price, price_decimal)
                order_dto.stop_loss = round(order_dto.stop_loss, price_decimal)
                order_dto.quantity = item["size"]
                print(order_dto)
                # order_dto.side = "Buy" if order_dto.side == "Sell" else "Buy"
                place_order(session,
                            order_dto,
                            market_out=False,
                            is_conditional=True)
                break
        
    return "StopLoss Shifted"