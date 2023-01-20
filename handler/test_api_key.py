from bybit_session import create_session
from logger import Logger

# Logger setup
logger_mod = Logger("API Tester")
logger = logger_mod.get_logger()

def h_test_api(dbcon, player_id):
    player_api = dbcon.get_player_api(player_id)[0]
    session = create_session(player_api['api_key'], player_api['api_secret'])
    try:
        ret = session.get_conditional_order(symbol="BTCUSDT")['ret_msg']
        if ret == "OK":
            return "Player API setup OK!"
        else:
            return "Connection Error"
    except Exception as e:
        logger.warning(e)
        return "API not setup correctly"