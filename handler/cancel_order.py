from bybit_session import create_session, cancel_order, cancel_pos, get_coin_info, order_preset, place_order
from dto.dto_order import dtoOrder
from logger import Logger

# Logger setup
logger_mod = Logger("Cancel Order")
logger = logger_mod.get_logger()

def h_cancel_order(dbcon, message_id):
    order_list = dbcon.get_related_oder(message_id)
    if order_list is None:
        return "Empty Row"
    coin = order_list[0]["coinpair"].replace("/","").strip()
    main_player_id = order_list[0]["player_id"]
    
    api_list = dbcon.get_followers_api(main_player_id)
    api_map = {}
    for i in range(len(api_list)):
        api_map[api_list[i]["follower_id"]] = api_list[i]
        
    current_id = api_list[0]["follower_id"]
    session = create_session(api_list[0]["api_key"], api_list[0]["api_secret"])

    my_pos = session.my_position(symbol=coin)["result"][0]
    qty = my_pos["size"]
    side = my_pos["side"]
    lev = get_coin_info(coin)["maxLeverage"]
    order_detail = dtoOrder(0,
                        coin,
                        side,
                        qty,
                        0,
                        0,
                        lev)
    order_preset(session, coin, lev)
    cancel_pos(session, coin)

    for i in order_list:
        if current_id != i["player_id"]:
            current_id = i["player_id"]
            session = create_session(api_map[i["player_id"]]["api_key"],
                                api_map[i["player_id"]]["api_secret"])
            my_pos = session.my_position(symbol=coin)["result"][0]                 
            order_detail.quantity = my_pos["size"]
            order_detail.side = my_pos["side"]
            order_preset(session, coin, lev)
            cancel_pos(session, coin)
        cancel_order(session, coin, i["follower_order"])
    return "Order Cancelled"
    