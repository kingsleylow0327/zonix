# bot.py
import asyncio
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
player_api_list = dbcon.get_all_player()
logger.info("Creating player websocket, Number: {}".format(len(player_api_list)))
for player in player_api_list:
    logger.info("Creating websocket, Player: {}".format(player['player_id']))
    try:
        ws_list[player['player_id']] = bybit_ws(player['api_key'], player['api_secret'])
    except Exception as e:
        logger.warning("Player {} is not connected: {}".format(player['player_id'], e))
logger.info("Done Creating websocket!")

def is_order(message):
    word_list = ['entry', 'tp', 'stop']
    pattern = '|'.join(word_list)
    matches = re.findall(pattern, message, re.IGNORECASE)
    return len(matches) == len(word_list)

def is_cancel(message):
    message_list = message.upper().split(" ")
    return message_list[0] == "CANCEL"

def is_market_out(message):
    message_list = message.upper().split(" ")
    return message_list[0] == "/MO"

def is_admin_cancel(message):
    message_list = message.upper().split(" ")
    return message_list[0] == "CANCEL" and len(message_list) > 1

def is_test(message):
    message_list = message.upper().split(" ")
    return message_list[0].strip() == "/FOLLOWSTATUS"

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
        if is_cancel(message.content):
            order_detail = dbcon.get_order_detail_by_order(message.channel.id)
            refer_id = order_detail["message_id"]
            order_msg_id = order_detail["order_msg_id"]
            reply_to = await CHANNEL.fetch_message(int(refer_id))
            # Check is admin and author
            if not dbcon.is_admin_and_order_author(refer_id, message.author.id):
                # Send message
                await message.channel.send("Permission Denied")
                return
            
            # Check status
            await CHANNEL.send("Cancel", reference=reply_to)
            ret = h_cancel_order(dbcon, order_msg_id) # cannot use refer_id, this id is from cornix, must get id from order_detail
            logger.info(ret)
            return
        
        if is_market_out(message.content):
            order_detail = dbcon.get_order_detail_by_order(message.channel.id)
            refer_id = order_detail["message_id"]
            order_msg_id = order_detail["order_msg_id"]
            coin_pair = order_detail["coinpair"].replace("/","").strip()
            reply_to = await CHANNEL.fetch_message(int(refer_id))
            # Check is admin and author
            if not dbcon.is_admin_and_order_author(refer_id, message.author.id):
                # Send message
                await message.channel.send("Permission Denied")
                return
            coin_price = h_check_price(coin_pair)
            await CHANNEL.send("Cancel", reference=reply_to)
            await message.channel.send(f"Market Out {coin_pair} Successfull at price: {str(coin_price)}")
            ret = h_cancel_order(dbcon, order_msg_id)
            logger.info(ret)
            return

    if message.channel.id == int(config.SENDER_CHANNEL_ID):
        if is_order(message.content): 
            ret = "Empty Row"

            # Create Thread
            reg_pat = re.search("(?i)(.*\n)(long|short)", message.content)
            coin_pair = reg_pat.group(1).strip()
            long_short = reg_pat.group(2).strip()
            cur_date = datetime.now().strftime('%h %d')
            thread_message = f'{cur_date} -- {coin_pair} {long_short} 🔴'
            f = await message.create_thread(name=thread_message)

            # Place Actual Order
            for i in range(MAX_TRIES):
                await asyncio.sleep(2)
                ret = h_place_order(dbcon, message.id)
                if ret == "Order Placed" or ret == "Order Placed (NR)":
                    break

            # Send feedback message on thread
            confirm_message = h_get_order_detail(dbcon, message.id)
            await f.send(confirm_message)
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

    # Receiver Channel Part
    # Channel Block
    if message.channel.id != int(config.RECEIVER_CHANNEL_ID):
        return

    # User Block
    if message.author.id != int(config.ZODIAC_ID):
        return
    
    if is_order(message.content):
        return
    
    msg_id = dbcon.get_order_msg_id(message.reference.message_id)["order_msg_id"]
    thread = client.get_channel(int(msg_id))
    await thread.send("System Msg: \n" + message.content)


client.run(config.TOKEN)