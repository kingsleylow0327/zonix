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

class TapbitOrder():
    def __init__(self, order, api_pair_list) -> None:
        self.api_pair_list = api_pair_list
        self.coin_pair = order["coinpair"].split("USD")[0].strip()

        self.coin_info = tutils.check_coin(self.coin_pair)
        if self.coin_info == None:
            logger.warning(f"{self.coin_pair} not found")
            raise Exception(f"{self.coin_pair} not found")
        
        self.max_lev = float(self.coin_info["max_leverage"])
        deci_place = '{0:.' + self.coin_info['price_precision'] + 'f}'
        
        self.multiplier = float(self.coin_info["multiplier"])
        
        self.order = order
        self.entry = deci_place.format(float(self.order["entry1"]))
        self.take_profit = deci_place.format(float(self.order["take_profit"])) if self.order["take_profit"] != None else ""
        self.stop_lost = deci_place.format(float(self.order["stop_lost"])) if self.order["stop_lost"] != None else ""
        
        self.direction = 'openShort' if self.order['long_short'] == 'SELL' else 'openLong'
        self.coin_qty_step = (self.max_lev/float(self.entry)) / self.multiplier
        self.sucess_number = 0
        self.failed_message = ""

    def h_tapbit_place_order(self):
        ret_json = {"message": "Order Placed"}
        if self.api_pair_list == None or len(self.api_pair_list) == 0:
            return "Alpha/Follower Error"

        session_list = [{"session":tapbit.SwapAPI(x["api_key"], x["api_secret"]),
            "role": x["role"], "player_id": x["follower_id"]} for x in self.api_pair_list]
        
        logger.info(f"Order Param: {json.dumps(self.order)}")

        # Asyncio Start here
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.asyn_place_tasks(session_list))
        logger.info(f"Order Failing Number: {len(session_list) - self.sucess_number}")
        logger.info("-------------")

        header_message = f"""
Order Json: {json.dumps(self.order)}

Total Player: {len(session_list)}
Failing Number: {len(session_list) - self.sucess_number} \n
"""
        ret_json["data"] = header_message
        if self.failed_message != "":
            ret_json["error"] = self.failed_message
        return ret_json

    async def asyn_place_order(self, item):
        try:
            wallet = item["session"].get_accounts()
            wallet = float(wallet["data"]["available_balance"])
            min_order = 2
            if wallet * (float(self.order.get("margin"))/100) > 2:
                min_order = wallet * (order_percent/100)

            qty = min_order * self.coin_qty_step
            tri = "latest" if self.stop_lost == "" else "mark"
            response = item["session"].order(self.coin_pair, 'crossed', self.direction, str(int(qty)), self.entry, str(int(self.max_lev)), 'limit', tp=self.take_profit, sl=self.stop_lost, tri=tri)
            if (response["message"] == None):
                self.sucess_number += 1
                logger.info(f"{item['player_id']} order Sucess!")
            else:
                self.failed_message += f"{item['player_id']} {response} \n"
                logger.error(f"{item['player_id']}: {response}")
        except Exception as e:
            exception_type, exception_object, exception_traceback = sys.exc_info()
            filename = os.path.split(exception_traceback.tb_frame.f_code.co_filename)[1]
            logger.error(f"{item['player_id']} attempt to place order but failed")
            logger.error(json.dumps(self.order))
            logger.error(f"{e} {exception_type} {filename}, Line {exception_traceback.tb_lineno}")
            self.failed_message += f"{item['player_id']}: {e} {exception_type} \n" 
        
    async def asyn_place_tasks(self, session_list):
        tasks = []
        for item in session_list:
            task = asyncio.create_task(self.asyn_place_order(item))
            tasks.append(task)
        await asyncio.gather(*tasks)