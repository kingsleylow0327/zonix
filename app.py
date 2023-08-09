# bot.py
import asyncio
import discord
from discord import app_commands
from interaction.register_box import RegisterBox
from interaction.follower_box import FollowerBox
from discord.ui import View
import re
import nest_asyncio

from config import Config
from datetime import datetime
from handler.tapbit_place_order import TapbitOrder
from handler.tapbit_cancel_order import TapbitCancel
from logger import Logger
from sql_con import ZonixDB

# Logger setup
logger_mod = Logger("Event")
logger = logger_mod.get_logger()

# Client setup
intents = discord.Intents.default()
intents.message_content = True

config = Config()

dbcon = ZonixDB(config)  
CHANNEL = None
GUILD_ID = int(config.GUILD_ID)
MAX_TRIES = 2
ws_list = {}
nest_asyncio.apply()

def is_tapbit_order(message):
    regex_pattern = r"(\!([^\s]+) )?(\#(\d{1,2})\% )?(([^\s]+) )\[(.*?)\] \$(\d+(?:\.\d{1,4})?)( \-(\$(\d+(?:\.\d{1,4})?)|(\d+(?:\.\d{1,2})?)%))?$"

    matches = re.match(regex_pattern, message, re.IGNORECASE)
    if matches:
        strategy = matches.group(2)
        if strategy:
            strategy = strategy.lower()
        else:
            strategy = config.ALPHA
        margin = matches.group(4) if matches.group(4) else 5
        symbol = matches.group(6)
        action = matches.group(7)
        amount = matches.group(8)
        stop_lost = matches.group(12)
        if stop_lost:
            multiplier = (1 + float(stop_lost)/100) if action.upper() == "SELL" else (1 - float(stop_lost)/100)
            stop_lost = float(amount) * multiplier
        return {"stratergy": strategy,
                "margin": margin, 
                "coinpair": symbol,
                "long_short": action.upper(),
                "entry1": amount,
                "stop_lost": stop_lost}
    
    return False

def is_tapbit_exit(message):
    regex_pattern = r"(\!([^\s]+) )?([^\s]+)USD (EXIT) (SHORT|LONG)$"
    matches = re.match(regex_pattern, message, re.IGNORECASE)
    if matches:
        stratergy = matches.group(2) if matches.group(2) else config.ALPHA
        symbol = matches.group(3).upper()
        action = matches.group(5).upper()
        return {"stratergy": stratergy,
                "symbol": symbol,
                "action": action}
    
    return False

class dis_client(discord.Client):
    def __init__(self, guild_id):
        super().__init__(intents=intents)
        self.synced = False
        self.guild_id = guild_id

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            await tree.sync(guild=discord.Object(id=self.guild_id))
            self.synced = True
        logger.info('Zonix Is Booted Up!')

aclient = dis_client(GUILD_ID)
tree = app_commands.CommandTree(aclient)

@aclient.event
async def on_message(message):
    if message.channel.id == int(config.SENDER_CHANNEL_ID):
        alpha=config.ALPHA
        sub_alpha = config.SUB_ALPHA.split(',')
        coin_pair = None
        if not (str(message.author.id) == alpha or str(message.author.id) in sub_alpha):
            return
        if is_tapbit_exit(message.content):
            order = is_tapbit_exit(message.content)
            thread_message = f'🔴 {message.content.upper()}'
            thread = await message.create_thread(name=thread_message)
            stratergy = order["stratergy"]
            side = order["action"]
            coin_pair = order["symbol"]
            api_pair_list = dbcon.get_followers_api(stratergy)
            cancel_obj = TapbitCancel(api_pair_list, coin_pair, side)
            ret = cancel_obj.h_tapbit_cancel_order()
            toArchive = True
            await thread.send(ret["data"])
            if ret["message"] == "Order Canceled":
                thread_message = f'🟢 {message.content.upper()}'
            if "order" in ret:
                thread_message = f'🟡 {message.content.upper()}'
                toArchive = False
                await thread.send(ret["order"])
            if "position" in ret:
                thread_message = f'🟡 {message.content.upper()}'
                toArchive = False
                await thread.send(ret["position"])

            await thread.edit(name=thread_message, archived=toArchive)
            return

        if is_tapbit_order(message.content):
            order = is_tapbit_order(message.content)
            cur_date = datetime.now().strftime('%h %d')
            thread_message = f'🔴 {cur_date} -- {order["coinpair"]} {order["long_short"]}'
            thread = await message.create_thread(name=thread_message)
            api_pair_list = dbcon.get_followers_api(order.get("stratergy"))
            order_obj = TapbitOrder(order, api_pair_list)
            ret = order_obj.h_tapbit_place_order()
            toArchive = True
            await thread.send(ret["data"])
            if ret["message"] == "Order Placed":
                thread_message = f'🟢 {cur_date} -- {order["coinpair"]} {order["long_short"]}'
            if "error" in ret:
                thread_message = f'🟡 {cur_date} -- {order["coinpair"]} {order["long_short"]}'
                toArchive = False
                await thread.send(ret["error"])

            await thread.edit(name=thread_message, archived=toArchive)
            return

# api function
@tree.command(guild=discord.Object(id=GUILD_ID), name='api')
async def api_command(interaction: discord.Interaction):
    modal = RegisterBox(dbcon)
    await interaction.response.send_modal(modal)

# follower function
@tree.command(guild=discord.Object(id=GUILD_ID), name='follower')
async def follower_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="ZRR Tapbit Bot",
        description="Select your preferance BOT",
        color=discord.Color.from_rgb(213, 86, 145)
    )
    
    view = View()
    view.add_item(FollowerBox(dbcon))
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    await asyncio.sleep(10)
    await interaction.delete_original_response()

@tree.command(guild=discord.Object(id=GUILD_ID), name='info')
async def info(interaction: discord.Interaction):
    data = dbcon.get_player_follower_and_api(interaction.user.id)

    if not data:
        await interaction.response.send_message("Opps...we can't find your info here", ephemeral=True)
        return
    
    embed = discord.Embed(
        title="ZRR Tapbit Bot",
        description=f"Your Bybit Api Key: **{data.get('api_key')}**\nYou are following: **{data.get('player_id')}**",
        color=discord.Color.from_rgb(213, 86, 145)
    )
    u = interaction.user
    userAvatar = u.avatar.url if u.avatar else u.default_avatar
    embed.set_author(name=u, icon_url=userAvatar)
    await interaction.response.send_message(u.mention, embed=embed, ephemeral=True)
    await asyncio.sleep(10)
    await interaction.delete_original_response()

aclient.run(config.TOKEN)
