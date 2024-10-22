# bot.py
import asyncio
import datetime as dt
import discord
import re

from bybit_websock import bybit_ws
from config import Config
from datetime import datetime
from handler.place_order import h_place_order
from handler.cancel_order import h_cancel_order, h_cancel_all
from handler.test_api_key import h_test_api
from handler.start_thread import h_get_order_detail
from handler.check_price import h_check_price
from handler.trading_stop import h_trading_stop
from handler.monthly_close import h_monthly_close_by_order_id
from dto.dto_order import dtoOrder
from logger import Logger
from sql_con import ZonixDB

# Logger setup
logger_mod = Logger("Event")
logger = logger_mod.get_logger()

# Client setup
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

config = Config()

dbcon = ZonixDB(config)  
CHANNEL = None
MAX_TRIES = 2
ws_list = {}
# player_api_list = dbcon.get_all_player()
# logger.info("Creating player websocket, Number: {}".format(len(player_api_list)))
# for player in player_api_list:
#     logger.info("Creating websocket, Player: {}".format(player['player_id']))
#     try:
#         ws_list[player['player_id']] = bybit_ws(player['api_key'], player['api_secret'])
#     except Exception as e:
#         logger.warning("Player {} is not connected: {}".format(player['player_id'], e))
# logger.info("Done Creating websocket!")

def is_order(message):
    word_list = ['entry', 'tp', 'stop']
    pattern = '|'.join(word_list)
    matches = re.findall(pattern, message, re.IGNORECASE)
    return len(matches) == len(word_list)

def is_cancel(message):
    message_list = message.upper().split(" ")
    return message_list[0] == "CANCEL" and len(message_list) == 1

def is_achieved_before(message):
    message_list = message.upper()
    return "ACHIEVED BEFORE" in message_list

def is_market_out(message):
    message_list = message.upper().split(" ")
    return message_list[0] == "MARKETOUT"

def is_admin_cancel(message):
    message_list = message.upper().split(" ")
    return message_list[0] == "CANCEL" and len(message_list) > 1

def is_monthly_close(message):
    message_list = message.upper().split(" ")
    return message_list[0] == "-CLOSE"

def is_test(message):
    message_list = message.upper().split(" ")
    return message_list[0].strip() == "/FOLLOWSTATUS"

def change_thread_name(old_name, emoji):
    new_name_list = old_name.split(" ")
    new_name_list[0] = emoji
    new_name = " ".join(new_name_list)
    return new_name

@client.event
async def on_ready():
    logger.info('Zonix Is Booted Up!')
    global CHANNEL
    CHANNEL = client.get_channel(int(config.RECEIVER_CHANNEL_ID))
    #await channel.send('Cornix Is Booted Up!')

@client.event
async def on_message(message):
    # Mesage in Thread 
    if isinstance(message.channel, discord.Thread):

        # Zonix ID block
        if message.author.id == int(config.ZONIX_ID) and not is_cancel(message.content):
            # Change Title
            if "all take-profit" in message.content.lower():
                order_detail = dbcon.get_order_detail_by_order(message.channel.id)
                h_cancel_order(dbcon, order_detail)
                new_name = change_thread_name(message.channel.name, "🤑")
                await message.channel.edit(name=new_name, archived=True)
                return
            if "take-profit" and "target 1" in message.content.lower():
                # Get Details
                order_detail = dbcon.get_order_detail_by_order(message.channel.id)
                order_msg_id = order_detail["order_msg_id"]
                player_id = order_detail["player_id"]
                order_dto = dtoOrder(order_detail["entry1"],
                                     order_detail["coinpair"].replace("/",""),
                                     order_detail["long_short"],
                                     "",
                                     "",
                                     order_detail["entry1"],
                                     "")
                # Cancel Active order
                ret = h_cancel_order(dbcon, order_detail, is_not_tp=False)
                print(ret)

                # Trading Stop
                ret = h_trading_stop(dbcon, player_id ,order_dto)
                print(ret)

                new_name = change_thread_name(message.channel.name, "🟢")
                await message.channel.edit(name=new_name)
                return
            if "stoploss" in message.content.lower():
                order_detail = dbcon.get_order_detail_by_order(message.channel.id)
                ret = h_cancel_order(dbcon, order_detail, is_not_tp=False)
                new_name = change_thread_name(message.channel.name, "💸")
                await message.channel.edit(name=new_name, archived=True)
                return
    
            if is_achieved_before(message.content):
                order_detail = dbcon.get_order_detail_by_order(message.channel.id)
                ret = h_cancel_order(dbcon, order_detail)
                logger.info(ret)
                thread_name = message.channel.name
                new_name = change_thread_name(thread_name, "⛔")
                await message.channel.edit(name=new_name, archived=True)
                return
            return

        if is_cancel(message.content):
            order_detail = dbcon.get_order_detail_by_order(message.channel.id)
            refer_id = order_detail["message_id"]
            order_msg_id = order_detail["order_msg_id"]
            order_status = order_detail["p_status"]
            reply_to = await CHANNEL.fetch_message(int(refer_id))
            # Check is admin and author
            if message.author.id != int(config.ZONIX_ID) and not dbcon.is_admin_and_order_author(refer_id, message.author.id):
                # Send message
                await message.channel.send("""🚨CANCEL UNSUCCESSFUL
No record found / wrong reply message\n""")
                return
            
            if order_status != "created":

                # Repeatative Cancel
                if order_status in ["cancelled", "completed", "break even", "stoploss"]:
                    await message.channel.send("""🚨CANCEL UNSUCCESSFUL
This TradeCall was cancelled earlier or closed\n""")
                    return
                
                # Reached Market Out
                await message.channel.send("""🚨CANCEL UNSUCCESSFUL
Cancel Failed, this TradeCall has reached Entry Price, use `MARKETOUT` instead.\n""")
                return
            
            # Check status
            await CHANNEL.send("Cancel", reference=reply_to)
            await message.channel.send("CANCEL SUCCESSFUL ❌ \n")
            ret = h_cancel_order(dbcon, order_detail) # cannot use refer_id, this id is from cornix, must get id from order_detail
            logger.info(ret)
            thread_name = message.channel.name
            new_name = change_thread_name(thread_name, "⛔")
            await message.channel.edit(name=new_name, archived=True)
            return
        
        if is_market_out(message.content):
            order_detail = dbcon.get_order_detail_by_order(message.channel.id)
            refer_id = order_detail["message_id"]
            order_msg_id = order_detail["order_msg_id"]
            coin_pair = order_detail["coinpair"].replace("/","").strip()
            order_status = order_detail["p_status"]
            reply_to = await CHANNEL.fetch_message(int(refer_id))
            # Check is admin and author
            if not dbcon.is_admin_and_order_author(refer_id, message.author.id):
                # Send message
                await message.channel.send("Permission Denied")
                return
            
            if order_status == "created":
                # Not yet reach TP
                await message.channel.send("""Market Out UNSUCCESSFUL
Market Out Failed, this TradeCall has NOT reached Entry Price, use `CANCEL` instead.\n""")
                return

            # Repeatative Market Out
            if order_status in ["cancelled", "completed", "break even", "stoploss"]:
                await message.channel.send("""🚨Market Out UNSUCCESSFUL
This TradeCall was cancelled earlier or closed\n""")
                return

            coin_price = h_check_price(coin_pair)
            await CHANNEL.send("Cancel", reference=reply_to)
            await message.channel.send(f"Market Out {coin_pair} Successfull at price: {str(coin_price)} \n")
            ret = h_cancel_order(dbcon, order_detail)
            dbcon.update_market_out_price(coin_price, refer_id)
            logger.info(ret)
            thread_name = message.channel.name
            new_name = change_thread_name(thread_name, "🆘")
            await message.channel.edit(name=new_name, archived=True)
            return

    if message.channel.id == int(config.SENDER_CHANNEL_ID):
        if is_order(message.content): 
            ret = "Empty Row"

            # Create Thread
            reg_pat = re.search("(?i)(.*\n)(long|short)", message.content)
            coin_pair = reg_pat.group(1).strip()
            long_short = reg_pat.group(2).strip()
            cur_date = datetime.now().strftime('%h %d')
            thread_message = f'🔴 {cur_date} -- {coin_pair} {long_short}'
            thread = await message.create_thread(name=thread_message)

            # Place Actual Order
            for i in range(MAX_TRIES):
                await asyncio.sleep(2)
                ret = h_place_order(dbcon, message.id)
                if ret == "Order Placed" or ret == "Order Placed (NR)":
                    break

            # Send feedback message on thread
            confirm_message = h_get_order_detail(dbcon, message.id)
            await thread.send(confirm_message)
            thread_message = f"🟡 {cur_date} -- {coin_pair} {long_short}"
            if confirm_message == "This order is not recognized":
                thread_message = f"🫥 {cur_date} -- {coin_pair} {long_short}"
                return
            await thread.edit(name=thread_message)
            logger.info(ret)
            return

    if message.channel.id == int(config.COMMAND_CHANNEL_ID):
        if is_test(message.content):
            message_list = message.content.split(" ")
            if dbcon.is_admin(message.author.id) and len(message_list) > 1 and "<@" in message_list[1]:
                player_id = "".join([c for c in message_list[1] if c.isdigit()])
                ret = h_test_api(dbcon, player_id, config.SERVER_IP)
                await message.channel.send(ret["msg"])
                return
            
            ret = h_test_api(dbcon, message.author.id, config.SERVER_IP)
            await message.author.send(ret["msg"])
            return

        if is_admin_cancel(message.content):
            if not dbcon.is_admin(message.author.id):
                logger.info("Not Admin")
                return

            message_list = message.content.upper().split(" ")
            if len(message_list) < 2:
                await message.channel.send("Missing Coin")
                return
            
            coin = message_list[2].replace("/", "")
            option = message_list[1]

            # Cancel Active Order
            if option == "-A":
                is_active = True
            
            # Cancel Posistion Order
            elif option == "-P":
                is_active = False

            ret = h_cancel_all(dbcon, coin, is_active)
            logger.info(ret)
            return
            
        # Monthly cancel
        if is_monthly_close(message.content):
            message_list = message.content.upper().split(" ")
            today = datetime.today()
            last_month = str(datetime(today.year, today.month-1, 1))
            this_month = str(datetime(today.year, today.month, 1) - dt.timedelta(0,1))
            
            # pass in order link id
            order_detail = h_monthly_close_by_order_id(dbcon, last_month, this_month)
            if order_detail == None:
                return
        
            for order in order_detail:
                message_id = order.get("order_msg_id")
                if message_id == None or message_id == "":
                    continue

                messagge = "MARKETOUT"
                if order.get("status") == "created":
                    messagge = "CANCEL"
                elif order.get("status") in ["completed", "cancelled", "Bot cancel", "Player Cancel", "stoploss", "trailing stoploss", "tp before entry"]:
                    continue
                
                # Get Thread by channel id
                thread = client.get_channel(int(message_id))
                if thread:
                    await thread.send(messagge)
            return

    # Receiver Channel Part
    # Channel Block
    if message.channel.id != int(config.RECEIVER_CHANNEL_ID):
        return

    # User Block
    if message.author.id != int(config.ZODIAC_ID):
        return
    
    if is_order(message.content):
        return

    if is_cancel(message.content):
        return

    msg_id = dbcon.get_order_msg_id(message.reference.message_id)["order_msg_id"]
    thread = client.get_channel(int(msg_id))
    await thread.send(message.content + "\n")


client.run(config.TOKEN)
