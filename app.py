# bot.py
import asyncio
import discord
import re

from bybit_websock import bybit_ws
from config import Config
from datetime import datetime
from handler.place_order import h_place_order, h_tapbit_place_order, h_tapbit_cancel_order
from handler.cancel_order import h_cancel_order, h_cancel_all
from handler.test_api_key import h_test_api
from handler.start_thread import h_get_order_detail
from handler.check_price import h_check_price
from handler.trading_stop import h_trading_stop
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

def is_tapbit_order(message):
    regex_pattern = r"^(.*?) \[(.*?)\] \$(\d+(?:\.\d{1,4})?)( \-(\$(\d+(?:\.\d{1,4})?)|(\d+(?:\.\d{1,2})?)%))?$"

    matches = re.match(regex_pattern, message, re.IGNORECASE)
    if matches:
        symbol = matches.group(1)
        action = matches.group(2)
        amount = matches.group(3)
        stop_lost = matches.group(6)
        if matches.group(7) :
            multiplier = (1 + float(matches.group(7))/100) if action.upper() == "SELL" else (1 - float(matches.group(7))/100)
            stop_lost = float(amount) * multiplier
        return {"coinpair": symbol, "long_short": action.upper(), "entry1": amount, "stop_lost": stop_lost}
    
    return False

def is_tapbit_exit(message):
    message_list = message.upper().split(" ")
    return "EXIT" in message_list

def is_order(message):
    word_list = ['entry', 'tp', 'stop']
    pattern = '|'.join(word_list)
    matches = re.findall(pattern, message, re.IGNORECASE)
    return len(matches) == len(word_list)

def is_cancel(message):
    message_list = message.upper().split(" ")
    return message_list[0] == "CANCEL"

def is_achieved_before(message):
    message_list = message.upper()
    return "ACHIEVED BEFORE" in message_list

def is_market_out(message):
    message_list = message.upper().split(" ")
    return message_list[0] == "MARKETOUT"

def is_admin_cancel(message):
    message_list = message.upper().split(" ")
    return message_list[0] == "CANCEL" and len(message_list) > 1

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
        if message.author.id == int(config.ZONIX_ID):
            # Change Title
            if "all take-profit" in message.content.lower():
                # Need cancel here
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
                ret = h_cancel_order(dbcon, order_msg_id, is_not_tp=False)
                print(ret)

                # Trading Stop
                ret = h_trading_stop(dbcon, player_id ,order_dto)
                print(ret)

                new_name = change_thread_name(message.channel.name, "🟢")
                await message.channel.edit(name=new_name)
                return
            if "stoploss" in message.content.lower():
                new_name = change_thread_name(message.channel.name, "💸")
                await message.channel.edit(name=new_name, archived=True)
                return
    
            if is_achieved_before(message.content):
                order_detail = dbcon.get_order_detail_by_order(message.channel.id)
                order_msg_id = order_detail["order_msg_id"]
                ret = h_cancel_order(dbcon, order_msg_id)
                logger.info(ret)
                thread_name = message.channel.name
                new_name = change_thread_name(thread_name, "⛔")
                await message.channel.edit(name=new_name, archived=True)
                return
            return

    if message.channel.id == int(config.SENDER_CHANNEL_ID):
        alpha=config.ALPHA
        sub_alpha = config.SUB_ALPHA.split(',')
        coin_pair = None
        if is_tapbit_exit(message.content) and (str(message.author.id) == alpha or str(message.author.id) in sub_alpha):
            message_list = message.content.upper().split(" ")
            side = None
            if "LONG" in message_list:
                side = "LONG"
            elif "SHORT" in message_list:
                side = "SHORT"
            if side == None:
                return
            
            for word in message_list:
                if "ETH" in word:
                    coin_pair = "ETH"
                    break
                elif "BTC" in word:
                    coin_pair = "BTC"
                    break
                elif "LINK" in word:
                    coin_pair = "LINK"
                    break
                else:
                    return
            ret = h_tapbit_cancel_order(alpha, dbcon, coin_pair, side)

        if is_tapbit_order(message.content):
            order = is_tapbit_order(message.content)
            cur_date = datetime.now().strftime('%h %d')
            thread_message = f'🔴 {cur_date} -- {order["coinpair"]} {order["long_short"]}'
            thread = await message.create_thread(name=thread_message)
            ret = h_tapbit_place_order(order, dbcon, config.ALPHA)
            if ret == "Order Placed":
                thread_message = f'🟢 {cur_date} -- {order["coinpair"]} {order["long_short"]}'
            else:
                thread_message = ret
                logger.info(ret)
            await thread.edit(name=thread_message)
            return            

        if is_order(message.content): 
            # ret = "Empty Row"

            # # Create Thread
            # reg_pat = re.search("(?i)(.*\n)(long|short)", message.content)
            # coin_pair = reg_pat.group(1).strip()
            # long_short = reg_pat.group(2).strip()
            # cur_date = datetime.now().strftime('%h %d')
            # thread_message = f'🔴 {cur_date} -- {coin_pair} {long_short}'
            # thread = await message.create_thread(name=thread_message)

            # # Place Actual Order
            # for i in range(MAX_TRIES):
            #     await asyncio.sleep(2)
            #     ret = h_tapbit_place_order(dbcon, message.id)
            #     if ret == "Order Placed" or ret == "Order Placed (NR)":
            #         break

            # # Send feedback message on thread
            # confirm_message = h_get_order_detail(dbcon, message.id)
            # await thread.send(confirm_message)
            # thread_message = f"🟡 {cur_date} -- {coin_pair} {long_short}"
            # if confirm_message == "This order is not recognized":
            #     thread_message = f"🫥 {cur_date} -- {coin_pair} {long_short}"
            #     return
            # await thread.edit(name=thread_message)
            # logger.info(ret)
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
