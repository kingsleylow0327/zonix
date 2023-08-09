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

def h_tapbit_place_order(order, dbcon):
    ret_json = {"message": "Order Placed"}
    api_pair_list = dbcon.get_followers_api(order.get("stratergy"))
    if api_pair_list == None or len(api_pair_list) == 0:
        return "Alpha/Follower Error"

    session_list = [{"session":tapbit.SwapAPI(x["api_key"], x["api_secret"]),
        "role": x["role"], "player_id": x["follower_id"]} for x in api_pair_list]

    coin_pair = order["coinpair"].split("USD")[0].strip()
    coin_info = tutils.check_coin(coin_pair)
    if coin_info == None:
        logger.warning(f"{coin_pair} not found")
        return "Coin Error"
    max_lev = float(coin_info["max_leverage"])
    multiplier = float(coin_info["multiplier"])

    coin_qty_step = (max_lev/float(order["entry1"])) / multiplier
    direction = 'openShort' if order['long_short'] == 'SELL' else 'openLong'
    price_pre = coin_info['price_precision']
    deci_place = '{0:.' + price_pre + 'f}'
    order["entry1"] = deci_place.format(float(order["entry1"]))
    stop_lost = ""
    if (order["stop_lost"] != None):
        stop_lost = deci_place.format(float(order["stop_lost"]))
        order["stop_lost"] = stop_lost
    logger.info(f"Order Param: {json.dumps(order)}")
    sucess_number = 0
    failed_message = ""

    async def asyn_place_tasks():
        async def asyn_place_order(item):
                try:
                    wallet = item["session"].get_accounts()
                    wallet = float(wallet["data"]["available_balance"])
                    min_order = 2
                    if wallet * (float(order.get("margin"))/100) > 2:
                        min_order = wallet * (order_percent/100)

                    qty = min_order * coin_qty_step
                    tri = "latest" if stop_lost == "" else "mark"
                    response = item["session"].order(coin_pair, 'crossed', direction, str(int(qty)), order["entry1"], str(int(max_lev)), 'limit', sl=stop_lost, tri=tri)
                    if (response["message"] == None):
                        sucess_number += 1
                        logger.info(f"{item['player_id']} order Sucess!")
                    else:
                        failed_message += f"{item['player_id']} {response} \n"
                        logger.error(f"{item['player_id']}: {response}")
                except Exception as e:
                    exception_type, exception_object, exception_traceback = sys.exc_info()
                    filename = os.path.split(exception_traceback.tb_frame.f_code.co_filename)[1]
                    logger.error(f"{item['player_id']} attempt to place order but failed")
                    logger.error(json.dumps(order))
                    logger.error(f"{e} {exception_type} {filename}, Line {exception_traceback.tb_lineno}")
                    failed_message += f"{item['player_id']}: {e} {exception_type} \n" 
        tasks = []
        for item in session_list:
            task = asyncio.create_task(asyn_place_order(item))
            tasks.append(task)
        await asyncio.gather(*tasks)

    asyncio.run(asyn_place_tasks())
    logger.info(f"Failing Number: {len(session_list) - sucess_number}")
    logger.info("-------------")

    header_message = f"""
Order Json: {json.dumps(order)}

Total Player: {len(session_list)}
Failing Number: {len(session_list) - sucess_number} \n
"""
    ret_json["data"] = header_message
    if failed_message != "":
        ret_json["error"] = failed_message
    return ret_json