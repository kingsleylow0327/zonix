from bybit_session import create_session
from logger import Logger

# Logger setup
logger_mod = Logger("API Tester")
logger = logger_mod.get_logger()

MIN_WALLET_USDT = 200

def h_test_api(dbcon, player_id, server_ip):
    player_api = dbcon.get_player_api(player_id)[0]
    follower_list = dbcon.get_follow_to(player_id)
    ERROR_MESSAGE = """
Player: {}
API Connection Error, suggest to do following steps:
1. Double Check your API Key and API Secrete
2. Set your API IP restricted Adress to **{}** ONLY
""".format("<@{}>".format(player_id), server_ip)

    try:
        session = create_session(player_api['api_key'], player_api['api_secret'])
        wallet_balance = session.get_wallet_balance(coin="USDT")['result']['USDT']['wallet_balance']
        ret = session.api_key_info()['result']
        ret_msg = """
Player: {}
API Key Permission: {}
Order: {}
Position: {}
USDC Contracts: {}
Derivatives API V3: {}
Restricted IP: {}

Wallet Balance >= 200: {}
Following: {}
"""
        api_info = None
        for item in ret:
            if item["api_key"] == player_api['api_key']:
                api_info = item
                break
        if api_info == None:
            return {"status":"OK", "msg": "No Such API"}
        i_api = i_ip = i_order = i_position = i_contract = i_d_v3 = i_wallet ="❌"
        i_follower = "None"
        if server_ip in api_info["ips"]:
            i_ip = "✅"
        if "Order" in api_info["permissions"]:
            i_order = "✅"
        if "Position" in api_info["permissions"]:
            i_position = "✅"
        if "OptionsTrade" in api_info["permissions"]:
            i_contract = "✅"
        if "DerivativesTrade" in api_info["permissions"]:
            i_d_v3 = "✅"
        if api_info["read_only"] == False:
            i_api = "✅"
        i_wallet = f"{wallet_balance}"
        
        if follower_list == None:
            i_follower = "Not Following anyone ❌"
        if len(follower_list) > 1:
            i_follower = "Following more than 1 player ❌"
        elif len(follower_list) == 1:
            i_follower = "<@{}>".format(follower_list[0]['player_id'])
            
        ret_msg = ret_msg.format("<@{}>".format(player_id), i_api, i_order, i_position, i_contract, i_d_v3, i_ip, i_wallet, i_follower)
        return {"status":"OK", "msg": ret_msg}
    except Exception as e:
        logger.warning(e)
        return {"status":"-1", "msg": ERROR_MESSAGE}