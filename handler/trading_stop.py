from bybit_session import create_session, shift_pos_stoploss
from sql_con import ZonixDB

def h_trading_stop(dbcon, player_id, order_dto):
    # Get related follower
    api_pair_list = dbcon.get_followers_api(player_id)
    if api_pair_list == None or len(api_pair_list) == 0:
        return "StopLoss Shifted (NR)"
    
    # Shift all stop loss
    for player in api_pair_list:
        session = create_session(player["api_key"], player["api_secret"])
        side = "Buy" if order_dto.side.upper() == "LONG" else "Sell"
        shift_pos_stoploss(session,
                           order_dto.symbol,
                           side,
                           order_dto.stoploss)
    return "StopLoss Shifted"