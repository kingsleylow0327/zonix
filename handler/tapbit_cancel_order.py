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


class TapbitCancel():
    def __init__(self, api_pair_list, coin_pair, side) -> None:
        self.coin_pair = coin_pair.upper()
        self.side = side.upper()
        self.api_pair_list = api_pair_list
        self.sucess_order = 0
        self.sucess_position = 0
        self.failed_order = ""
        self.failed_position = ""
        self.order_json = {"coin" : self.coin_pair, "side" : self.side}
        self.h_tapbit_cancel_order()

    def h_tapbit_cancel_order(self):
        ret_json = {"message": "Order Canceled"}
        if self.api_pair_list == None or len(self.api_pair_list) == 0:
            return "Order Placed (NR)"
        
        session_list = [{"session":tapbit.SwapAPI(x["api_key"], x["api_secret"]),
            "role": x["role"], "player_id": x["follower_id"]} for x in self.api_pair_list]
        
        # Asyncio Start here
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.asyn_cancel_tasks(session_list))
        header_message = f"""
Order Json: {json.dumps(self.order_json)}

Total Player: {len(session_list)}
Failing Order: {len(session_list) - self.sucess_order}
Failing Position: {len(session_list) - self.sucess_position} \n
"""
        ret_json["data"] = header_message
        if self.failed_order != "":
            ret_json["order"] = "Failing Order: \n" + self.failed_order
        if self.failed_position != "":
            ret_json["position"] = "Failing Position: \n" + self.failed_position
        return ret_json

    async def asyn_cancel_order(self, item):
        try:
            order_list = item["session"].get_order_list(self.coin_pair)["data"]
            if len(order_list) != 0:
                for order in order_list:
                    if self.coin_pair in order["contract_code"] and self.side in order["direction"].upper():
                        response = item["session"].cancel(order["order_id"])
                        if (response["message"] == None):
                            self.sucess_order += 1
                        else:
                            self.failed_order += f"{item['player_id']} {response} \n"
            else:
                self.sucess_order += 1

        except Exception as e:
            exception_type, exception_object, exception_traceback = sys.exc_info()
            filename = os.path.split(exception_traceback.tb_frame.f_code.co_filename)[1]
            logger.error(f"{item['player_id']} attempt to close order but failed")
            logger.error(f"{e} {exception_type} {filename}, Line {exception_traceback.tb_lineno}")
            self.failed_order += f"{item['player_id']}: {e} {exception_type} \n" 
        
        try:
            position = item["session"].get_position(self.coin_pair)["data"]
            quantity = '0'
            if len(position) != 0:
                for pos in position:
                    if "market_price" not in self.order_json:
                        self.order_json["mark_price"] = pos["mark_price"]
                    if pos["side"].upper() == self.side and pos["quantity"] != "0":
                        quantity = pos["quantity"]
                        break
                if quantity == '0':
                    self.sucess_position += 1
                    logger.warning(f'{item["player_id"]} TPSL not placed due to no position')
                    return

                direction = 'closeShort' if self.side == 'SHORT' else 'closeLong'
                response = item["session"].order(self.coin_pair, 
                                'crossed', 
                                direction, 
                                str(quantity), 
                                str(pos["mark_price"]), 
                                str(pos['leverage']), 
                                'market')
                if (response["message"] == None):
                    self.sucess_position += 1
                else:
                    self.failed_position += f"{item['player_id']} {response} \n"

            else:
                self.sucess_position += 1

        except Exception as e:
            exception_type, exception_object, exception_traceback = sys.exc_info()
            filename = os.path.split(exception_traceback.tb_frame.f_code.co_filename)[1]
            logger.error(f"{item['player_id']} attempt to close order but failed")
            logger.error(f"{e} {exception_type} {filename}, Line {exception_traceback.tb_lineno}")
            self.failed_position += f"{item['player_id']}: {e} {exception_type} \n"        
    
    async def asyn_cancel_tasks(self, session_list):
        tasks = []
        for item in session_list:
            task = asyncio.create_task(self.asyn_cancel_order(item))
            tasks.append(task)
        await asyncio.gather(*tasks)

