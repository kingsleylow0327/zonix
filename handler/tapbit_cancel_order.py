import asyncio
import os
import sys
import json
import tapbit.swap_api as tapbit
import tapbit.utils as tutils
from logger import Logger

logger_mod = Logger("Place Order")
logger = logger_mod.get_logger()
order_percent = 5

def h_tapbit_cancel_order(author, dbcon, coin_pair, side=None):
    ret_json = {"message": "Order Canceled"}
    sucess_order = 0
    sucess_position = 0
    failed_order = ""
    failed_position = ""
    side=side.upper()
    coin_pair = coin_pair.upper()
    api_pair_list = dbcon.get_followers_api(author)
    order_json = {"coin" : coin_pair, "side" : side}
    if api_pair_list == None or len(api_pair_list) == 0:
        return "Order Placed (NR)"
    
    session_list = [{"session":tapbit.SwapAPI(x["api_key"], x["api_secret"]),
        "role": x["role"], "player_id": x["follower_id"]} for x in api_pair_list]
    
    async def asyn_cancel_order(item):
        try:
            order_list = item["session"].get_order_list(coin_pair)["data"]
            if len(order_list) != 0:
                for order in order_list:
                    if coin_pair in order["contract_code"] and side in order["direction"].upper():
                        response = item["session"].cancel(order["order_id"])
                        if (response["message"] == None):
                            sucess_order += 1
                        else:
                            failed_order += f"{item['player_id']} {response} \n"
            else:
                sucess_order += 1

        except Exception as e:
            exception_type, exception_object, exception_traceback = sys.exc_info()
            filename = os.path.split(exception_traceback.tb_frame.f_code.co_filename)[1]
            logger.error(f"{item['player_id']} attempt to close order but failed")
            logger.error(f"{e} {exception_type} {filename}, Line {exception_traceback.tb_lineno}")
            failed_order += f"{item['player_id']}: {e} {exception_type} \n" 
        
        try:
            position = item["session"].get_position(coin_pair)["data"]
            quantity = '0'
            if len(position) != 0:
                for pos in position:
                    if "market_price" not in order_json:
                        order_json["mark_price"] = pos["mark_price"]
                    if pos["side"].upper() == side and pos["quantity"] != "0":
                        quantity = pos["quantity"]
                        break
                if quantity == '0':
                    sucess_position += 1
                    logger.warning(f'{item["player_id"]} TPSL not placed due to no position')
                    return

                direction = 'closeShort' if side == 'SHORT' else 'closeLong'
                response = item["session"].order(coin_pair, 
                                'crossed', 
                                direction, 
                                str(quantity), 
                                str(pos["mark_price"]), 
                                str(pos['leverage']), 
                                'market')
                if (response["message"] == None):
                    sucess_position += 1
                else:
                    failed_position += f"{item['player_id']} {response} \n"

            else:
                sucess_position += 1

        except Exception as e:
            exception_type, exception_object, exception_traceback = sys.exc_info()
            filename = os.path.split(exception_traceback.tb_frame.f_code.co_filename)[1]
            logger.error(f"{item['player_id']} attempt to close order but failed")
            logger.error(f"{e} {exception_type} {filename}, Line {exception_traceback.tb_lineno}")
            failed_position += f"{item['player_id']}: {e} {exception_type} \n"        
    
    async def asyn_cancel_tasks():
        tasks = []
        for item in session_list:
            task = asyncio.create_task(asyn_cancel_order(item))
            tasks.append(task)
        await asyncio.gather(*tasks)

    asyncio.run(asyn_cancel_tasks())
    header_message = f"""
Order Json: {json.dumps(order_json)}

Total Player: {len(session_list)}
Failing Order: {len(session_list) - sucess_order}
Failing Position: {len(session_list) - sucess_position} \n
"""
    ret_json["data"] = header_message
    if failed_order != "":
        ret_json["order"] = "Failing Order: \n" + failed_order
    if failed_position != "":
        ret_json["position"] = "Failing Position: \n" + failed_position
    return ret_json
