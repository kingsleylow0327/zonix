import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def close_all_order(player_session, coin_pair, side=None):
    response = player_session.close_all_order(coin_pair, side)
    
    return response

async def close_all_position(player_session, coin_pair, side):
    response = player_session.close_all_pos(coin_pair, side)
    
    return response

async def close_order(player_session, coin_pair, order_list):
    response = player_session.close_order(coin_pair, order_list)
    
    return response

async def place_order(player_session, order_list):
    response = player_session.place_order(order_list)
    
    return response

async def get_position(player_session, coin_pair):
    response = player_session.get_position(coin_pair)
    
    return response

async def get_price(player_session, coin_pair):
    response = player_session.get_price(coin_pair).get("data").get("price")
    
    return response

async def get_all_pending(player_session, coin_pair):
    response = player_session.get_all_pending(coin_pair)
    
    return response

async def get_all_pending(player_session, coin_pair):
    response = player_session.get_all_pending(coin_pair)
    
    return response

async def place_single_order(player_session, order_json):
    response = player_session.place_single_order(order_json)

    return response

async def get_coin_info(player_session, coin_pair):
    response = player_session.get_coin_info(coin_pair).get("data")[0]

    return response

async def get_wallet(player_session):
    response = player_session.get_wallet().get("data").get("balance").get("availableMargin")

    return response

async def order_preset(player_session, coin_pair):
    response = player_session.order_preset(coin_pair)

    return response