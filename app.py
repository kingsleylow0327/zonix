# bot.py
import asyncio
import discord

from bybit_websock import bybit_ws
from config import Config
from handler.place_order import h_place_order
from handler.cancel_order import h_cancel_order
from handler.test_api_key import h_test_api
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
    return "Leverage Cross x25" in message

def is_cancel(message):
    message_list = message.upper().split(" ")
    return message_list[0] == "CANCEL"

def is_test(message):
    message_list = message.upper().split(" ")
    return message_list[0].strip() == "/PINGAPI"

@client.event
async def on_ready():
    logger.info('Zonix Is Booted Up!')
    global CHANNEL
    CHANNEL = client.get_channel(int(config.RECEIVER_CHANNEL_ID))
    #await channel.send('Cornix Is Booted Up!')

@client.event
async def on_message(message):
    if message.channel.id == int(config.SENDER_CHANNEL_ID):
        if is_test(message.content):
            ret = h_test_api(dbcon, message.author.id, config.SERVER_IP)
            await message.channel.send(ret)
            logger.info(ret)
        return

    # Channel Block
    if message.channel.id != int(config.RECEIVER_CHANNEL_ID):
        print("Not Channel: {}".format(message.channel.id))
        return

    # User Block
    if message.author.id != int(config.ZODIAC_ID):
        print("Not Author: {}".format(message.author.id))
        return
    
    if is_cancel(message.content):
        ret = h_cancel_order(dbcon, message.reference.message_id)
        logger.info(ret)
        return

    if not is_order(message.content):
        return
    
    print("Placing order")
    ret = "Empty Row"
    for i in range(2):
        await asyncio.sleep(2)
        ret = h_place_order(dbcon, message.id)
        if ret == "Order Placed":
            break

    logger.info(ret)

client.run(config.TOKEN)