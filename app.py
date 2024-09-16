# bot.py
import asyncio
import datetime as dt
from decimal import Decimal, ROUND_HALF_UP
import discord
import re

from config import Config
from datetime import datetime
from handler.bingx_place_order import h_bingx_order
from handler.bingx_stratery_place_order import h_bingx_strategy_order
from handler.bingx_cancel_order import h_bingx_cancel_order, h_bingx_cancel_all
from handler.bingx_safety_pin import h_bingx_safety_pin
from handler.bingx_ptp import h_bingx_ptp
from handler.test_api_key import h_test_api
from handler.start_thread import h_get_order_detail
from handler.monthly_close import h_monthly_close_by_order_id
from logger import Logger
from random import randint
from sql_con import ZonixDB
from telegram_forward.tele_bot import forward_order_to_telegram, forward_update_to_telegram, forward_picture
from util import spilt_discord_message, random_forward_order_message

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
SENDER_CHANNEL_LIST = None
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


def is_strategy(message):
    # Strategy Example: !BETA #10% BTCUSDT [Buy] $60000 -1.5% +3% /62000 >0.5%
    # Strategy Format:  !<Strategy> #<Wallet Margin> <Coin Pair> [Order Action] $<Entry Price> -<Stop Lost> +<Take Profit> /<Trailing Stop Price> ><Trailing Stop Percentage>%
    regex_pattern = re.compile(
        r"^!"                                                   # Start with an exclamation mark.
        r"(?P<strategy>[A-Za-z0-9]+)\s"                         # Strategy
        r"#(?P<wallet_margin>\d+(\.\d+)?)%\s?"                  # Wallet Margin - starts with a '#', one or more digits, ending with a '%'.
        r"(?P<coin_pair>[A-Za-z]+)\s"                           # Coin Pair - Upper/Lower case characters
        r"\[(?P<order_action>([Bb]uy|[Ss]ell))\]\s"             # Order Action - 'Buy' or 'Sell' enclosed in square brackets
        r"(\$(?P<entry_price>\d+(\.\d+)?))?\s?"                 # Entry Price, which starts with a '$'
        r"-(?P<stop_loss>\d+(\.\d+)?)%\s"                       # Stop Loss - Can be percentage with ends with % or whole value with decimal
        r"(\+(?P<take_profit>\d+(\.\d+)?%?))?\s?"               # Take profit (Optional) - Can be percentage with ends with % or whole value with decimal
        r"/(?P<trailing_stop_price>\d+(\.\d+)?)%\s"             # Trailing Stop Price - Starts with '/'
        r">(?P<trailing_stop_percentage>\d+(\.\d+)?)%$"         # Trailing Stop Percentage - Starts with '>', ends with '%'
    )

    match = re.match(regex_pattern, message)

    if match:
        strategy = match.group("strategy")
        wallet_margin = match.group("wallet_margin")
        coin_pair = match.group("coin_pair")
        order_action = match.group("order_action")
        entry_price = float(match.group("entry_price")) if match.group("entry_price") else None # Convert to float
        # stop_loss = float(convert_percentage_value_to_value(entry_price, match.group("stop_loss")))
        stop_loss = float(match.group("stop_loss"))
        # take_profit = convert_percentage_value_to_value(entry_price, match.group("take_profit"))
        trailing_stop_price = float(match.group("trailing_stop_price"))  # Convert to float
        trailing_stop_percentage = match.group("trailing_stop_percentage")

        return {
            "strategy": strategy.lower(),
            "margin": wallet_margin,
            "coin_pair": coin_pair.upper(),
            "order_action": "LONG" if order_action.upper() == "BUY" else "SHORT",  # Convert to LONG/SHORT
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            # "take_profit": take_profit,
            "trailing_stop_price": trailing_stop_price,
            "trailing_stop_percentage": trailing_stop_percentage
        }
    return None

def is_order(message):
    word_list = ['entry', 'tp', '\\bstop\\b(?![a-zA-Z])']
    pattern = '|'.join(word_list)
    matches = re.findall(pattern, message, re.IGNORECASE)
    return len(matches) == len(word_list)

def is_entry(message):
    return "Average Entry Price" in message

def is_cancel(message):
    message_list = message.upper().split(" ")
    return message_list[0] == "CANCEL" and len(message_list) == 1

def is_sp(message):
    message_list = message.upper().split(" ")
    return message_list[0] == "SP" and len(message_list) == 1

def is_ptp(message):
    message_list = message.upper().split(" ")
    return message_list[0] == "PTP" and len(message_list) == 1

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
    global ERROR_CHANNEL
    ERROR_CHANNEL = client.get_channel(int(config.ERROR_CHANNEL_ID))
    global SENDER_CHANNEL_LIST
    SENDER_CHANNEL_LIST = [int(s) for s in config.SENDER_CHANNEL_ID.split(",")]
    #await channel.send('Cornix Is Booted Up!')

@client.event
async def on_message(message):
    # Message in Thread
    if isinstance(message.channel, discord.Thread):

        # Zonix ID block
        if message.author.id == int(config.ZONIX_ID) and not is_cancel(message.content) and not is_market_out(message.content) and not is_sp(message.content) and not is_ptp(message.content):
            # Change Title
            if "all take-profit" in message.content.lower():
                order_detail = dbcon.get_order_detail_by_order(message.channel.id)
                ret = h_bingx_cancel_order(dbcon, order_detail)
                new_name = change_thread_name(message.channel.name, "🤑")
                if ret.get("error") and ret.get("error") != []:
                    for error in spilt_discord_message(ret.get("error")):
                        await message.channel.send(error)
                        logger.info(error)
                await message.channel.edit(name=new_name, archived=True)
                forward_update_to_telegram("🤑PROFIT🤑", dbcon, config, message.channel.id, message.content)
                return

            if "take-profit" in message.content.lower() and "target 1" in message.content.lower():
                # Get Details
                order_detail = dbcon.get_order_detail_by_order(message.channel.id)
                player_id = order_detail["player_id"]
                ret = h_bingx_cancel_order(dbcon, order_detail, is_not_tp=False)
                new_name = change_thread_name(message.channel.name, "🟢")
                if ret.get("error") and ret.get("error") != []:
                    for error in spilt_discord_message(ret.get("error")):
                        await message.channel.send(error)
                        logger.info(error)
                await message.channel.edit(name=new_name)
                forward_update_to_telegram("🤑PROFIT🤑", dbcon, config, message.channel.id, message.content)
                return

            if "stoploss" in message.content.lower():
                order_detail = dbcon.get_order_detail_by_order(message.channel.id)
                ret = h_bingx_cancel_order(dbcon, order_detail, is_not_tp=True)
                new_name = change_thread_name(message.channel.name, "💸")
                if ret.get("error") and ret.get("error") != []:
                    for error in spilt_discord_message(ret.get("error")):
                        await message.channel.send(error)
                        logger.info(error)
                await message.channel.edit(name=new_name, archived=True)
                return
            
            if "stop target hit" in message.content.lower():
                order_detail = dbcon.get_order_detail_by_order(message.channel.id)
                ret = h_bingx_cancel_order(dbcon, order_detail, is_not_tp=True)
                new_name = change_thread_name(message.channel.name, "❌")
                if ret.get("error") and ret.get("error") != []:
                    for error in spilt_discord_message(ret.get("error")):
                        await message.channel.send(error)
                        logger.info(error)
                await message.channel.edit(name=new_name, archived=True)
                return
    
            if is_achieved_before(message.content):
                order_detail = dbcon.get_order_detail_by_order(message.channel.id)
                ret = h_bingx_cancel_order(dbcon, order_detail)
                new_name = change_thread_name(message.channel.name, "⛔")
                if ret.get("error") and ret.get("error") != []:
                    for error in spilt_discord_message(ret.get("error")):
                        await message.channel.send(error)
                        logger.info(error)
                await message.channel.edit(name=new_name, archived=True)
                return
            
            # if is_entry(message.content):
                # forward_update_to_telegram("✅ENTRY✅", dbcon, config, message.channel.id, message.content)
            return
        
        if is_sp(message.content):
            order_detail = dbcon.get_order_detail_by_order(message.channel.id)
            refer_id = order_detail["message_id"]
            if not dbcon.is_admin_and_order_author(refer_id, message.author.id):
                # Send message
                await message.channel.send("Permission Denied")
                return
            coin_pair = order_detail["coinpair"].strip().replace("/","").replace("-","").upper()
            coin_pair = coin_pair[:-4] + "-" + coin_pair[-4:]
            order_status = order_detail["p_status"]

            # Yet to enter
            if order_status in ["created"]:
                await message.channel.send("""Safety Pin UNSUCCESSFUL
This TradeCall has not reached Entry\n""")
                return

            # Done Order Block
            if order_status in ["cancelled", "completed", "break even", "stoploss"]:
                await message.channel.send("""Safety Pin UNSUCCESSFUL
This TradeCall was cancelled earlier or closed\n""")
                return
            
            await message.channel.send("Setting Safety Pin")
            ret = h_bingx_safety_pin(dbcon, order_detail)
            if ret.get("error") and ret.get("error") != []:
                for error in spilt_discord_message(ret.get("error")):
                    await message.channel.send(error)
                    logger.info(error)
            
            await message.channel.send(f"Set SP Successfull \n")
            return
        
        if is_ptp(message.content):
            order_detail = dbcon.get_order_detail_by_order(message.channel.id)
            refer_id = order_detail["message_id"]
            if not dbcon.is_admin_and_order_author(refer_id, message.author.id):
                # Send message
                await message.channel.send("Permission Denied")
                return
            coin_pair = order_detail["coinpair"].strip().replace("/","").replace("-","").upper()
            coin_pair = coin_pair[:-4] + "-" + coin_pair[-4:]
            order_status = order_detail["p_status"]

            # Done Order Block
            if order_status in ["cancelled", "completed", "break even", "stoploss"]:
                await message.channel.send("""PTP UNSUCCESSFUL
This TradeCall was cancelled earlier or closed\n""")
                return
            
            await message.channel.send("Placing PTP...")
            ret = h_bingx_ptp(dbcon, order_detail)
            if ret.get("error") and ret.get("error") != []:
                for error in spilt_discord_message(ret.get("error")):
                    await message.channel.send(error)
                    logger.info(error)
            
            await message.channel.send(f"PTP Successfull, SL Price reset(based on original order)\n")
            return

        if is_cancel(message.content):
            order_detail = dbcon.get_order_detail_by_order(message.channel.id)
            if not order_detail:
                await message.channel.send("Error: Missing Order Detail, please contact admin \n")
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
            await message.channel.send("CANCEL IN PROGRESS... \n")
            ret = h_bingx_cancel_order(dbcon, order_detail) # cannot use refer_id, this id is from cornix, must get id from order_detail
            logger.info(ret.get("msg"))
            if ret.get("error") and ret.get("error") != []:
                await message.channel.send(f"MsgId - {order_detail['message_id']} having following Error: \n")
                for error in spilt_discord_message(ret.get("error")):
                    await message.channel.send(error)
                    logger.info(error)
            await message.channel.send("CANCEL SUCCESSFUL ❌ \n")
            new_name = change_thread_name(message.channel.name, "⛔")
            await message.channel.edit(name=new_name, archived=True)
            # forward_update_to_telegram("CANCEL", dbcon, config, message.channel.id)
            return
        
        if is_market_out(message.content):
            order_detail = dbcon.get_order_detail_by_order(message.channel.id)
            refer_id = order_detail["message_id"]
            order_msg_id = order_detail["order_msg_id"]
            coin_pair = order_detail["coinpair"].strip().replace("/","").replace("-","").upper()
            coin_pair = coin_pair[:-4] + "-" + coin_pair[-4:]
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
            
            await CHANNEL.send("Cancel", reference=reply_to)
            ret = h_bingx_cancel_order(dbcon, order_detail)
            if ret.get("error") and ret.get("error") != []:
                for error in spilt_discord_message(ret.get("error")):
                    await message.channel.send(error)
                    logger.info(error)
            coin_price = ret.get("price")
            await message.channel.send(f"Market Out {coin_pair} Successfull at price: {str(coin_price)} \n")
            dbcon.update_market_out_price(coin_price, refer_id)
            thread_name = message.channel.name
            new_name = change_thread_name(thread_name, "🆘")
            await message.channel.edit(name=new_name, archived=True)
            # forward_update_to_telegram("MARKET OUT", dbcon, config, message.channel.id)
            return

    if message.channel.id in SENDER_CHANNEL_LIST:
        if order := is_strategy(message.content):
            cur_date = datetime.now().strftime('%h %d')
            thread_message = f'🔴 {cur_date} -- {order.get("coin_pair")} {order.get("coin_pair")}'
            thread = await message.create_thread(name=thread_message)
            await thread.send("Order In Progress... \n")
            ret = h_bingx_strategy_order(dbcon, order, message.author.id, message.id)
            if ret.get("error") and ret.get("error") != []:
                await thread.send(f"MsgId - {message.id} having following Error: \n")
                for error in spilt_discord_message(ret.get("error")):
                    await thread.send(error)
                    logger.info(error)
                    
                if ret.get("status") and ret.get("status") == 400:
                    await thread.send("Order skipped ❌ due to not registered strategy \n")
                else:
                    await thread.send("Order SUCCESSFUL ✅ \n")
                    thread_message = f'🟡 {cur_date} -- {order.get("coin_pair")} {order.get("coin_pair")}'
            
            else:
                await thread.send("Order SUCCESSFUL ✅ \n")
                thread_message = f'🟢 {cur_date} -- {order.get("coin_pair")} {order.get("coin_pair")}'
            
            await thread.edit(name=thread_message, archived=True)

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
            await thread.send("Order In Progress... \n")
            for i in range(MAX_TRIES):
                await asyncio.sleep(2)
                # ret = h_place_order(dbcon, message.id)
                ret = h_bingx_order(dbcon, message.id)
                if ret.get("msg") == "Order Placed" or ret == "Order Placed (NR)":
                    break

            # Send feedback message on thread
            confirm_message = h_get_order_detail(dbcon, message.id)
            thread_message = f"🟡 {cur_date} -- {coin_pair} {long_short}"
            if confirm_message == "This order is not recognized":
                thread_message = f"🫥 {cur_date} -- {coin_pair} {long_short}"
                return
            await thread.send(confirm_message)
            if ret.get("error") and ret.get("error") != []:
                await thread.send(f"MsgId - {message.id} having following Error: \n")
                for error in spilt_discord_message(ret.get("error")):
                    await thread.send(error)
                    logger.info(error)
            await thread.send("Order SUCCESSFUL ✅ \n")
            await thread.edit(name=thread_message)
            tele_random = randint(1, 100)
            if tele_random > 50:
                forward_order_to_telegram(config, message.content, message.author.display_name, message.id)
                random_order_channel = client.get_channel(int(config.RANDOM_ORDER_CHANNEL_ID))
                await random_order_channel.send(random_forward_order_message(message.content, message.id))
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

            ret = h_bingx_cancel_all(dbcon, coin, is_active)
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

    if message.channel.id == int(config.PNL_CHANNEL_ID):
        attachments = message.attachments
        for attachment in attachments:
            if attachment.content_type not in ['image/avif', 'image/jpeg', 'image/png', 'image/svg+xml', 'image/tiff']:
                continue
            attachment_url = attachment.url
            forward_picture(config,attachment_url)
    
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
    
    if message.reference:
        msg_id_obj = dbcon.get_order_msg_id(message.reference.message_id)
        if not msg_id_obj:
            error_msg = "Missing Reference Message"
            error_msg_content = message.content
            await ERROR_CHANNEL.send(f"Error: {error_msg} \n Error Message: {error_msg_content}")
            return
        msg_id = msg_id_obj.get("order_msg_id")
        if not msg_id_obj:
            error_msg = "Missing message id"
            error_msg_content = message.content
            await ERROR_CHANNEL.send(f"Error: {error_msg} \n Error Message: {error_msg_content}")
            return
        thread = client.get_channel(int(msg_id))
        if thread:
            await thread.send(message.content + "\n")


client.run(config.TOKEN)
