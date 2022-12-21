# bot.py
import asyncio
import discord

from bybit_con import create_session
from config import Config
from handler.place_order import h_place_order
from logger import Logger
from sql_con import ZonixDB

# Logger setup
logger_mod = Logger("Initialized")
logger = logger_mod.get_logger()

# Client setup
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

config = Config()

dbcon = ZonixDB(config)  
CHANNEL = None
session = create_session(config.BYBIT_API_KEY, config.BYBIT_API_SECRET)

def is_order(message):
    return "Leverage Cross x25" in message

@client.event
async def on_ready():
    logger.info('Zonix Is Booted Up!')
    global CHANNEL
    CHANNEL = client.get_channel(int(config.RECEIVER_CHANNEL_ID))
    #await channel.send('Cornix Is Booted Up!')

@client.event
async def on_message(message):
    # Channel Block
    if message.channel.id != int(config.RECEIVER_CHANNEL_ID):
        return

    # User Block
    if message.author.id != int(config.ZODIAC_ID):
        return
    
    if not is_order(message.content):
        return
    
    ret = "Empty Row"
    for i in range(2):
        await asyncio.sleep(2)
        ret = h_place_order(dbcon, session, message.id)
        if ret == "Order Placed":
            break

    logger.info(ret)

client.run(config.TOKEN)