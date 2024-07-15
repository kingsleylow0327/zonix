import re
import requests

def forward_order_to_telegram(config, order_message: str, author: str, id: str):
    api = config.TELEGRAM_API
    channel = config.TELEGRAM_CHANNEL
    topic = config.TELEGRAM_TRADECALL_TOPIC
    final_message = message_order_wrapper(order_message, id)
    webhook = f'https://api.telegram.org/bot{api}/sendMessage'
    body = {"message_thread_id": topic,
            'chat_id': f'{channel}_{topic}',
            "parse_mode":"html",
            "disable_web_page_preview": "true",
            "text":final_message}
    # body = {'chat_id': f'{channel}', "parse_mode":"html", "text":final_message, "disable_web_page_preview": "true"}  # for testing
    r = requests.get(webhook, json = body)

def forward_update_to_telegram(type: str, dbcon, config, order_id: str, update_message=""):
    player_order = dbcon.get_order_message_by_order_msg_id(order_id)
    api = config.TELEGRAM_API
    channel = config.TELEGRAM_CHANNEL
    topic = config.TELEGRAM_TRADECALL_TOPIC
    if not player_order:
        return
    order_message = player_order.get("message")
    order_message_list = order_message.split("\n")[0:-2]
    order_message_list[2:4] = []
    order_message = "\n".join(order_message_list)

    author = player_order.get("player_name")
    if type not in ["CANCEL", "MARKET OUT"]:
        update_message = f"\n\n{update_message}\n\n"
    profit = "🤑"
    reg_pat = re.search("(?i)profit:\s*([0-9,.]+%?)", update_message)
    profit = reg_pat.group(1).strip()
    final_message = message_update_wrapper(order_message, order_id, profit)
    final_message = final_message.replace("#", "")
    body = {"message_thread_id": topic,
            'chat_id': f'{channel}_{topic}',
            "parse_mode":"html",
            "disable_web_page_preview": "true",
            "text":final_message}
    # body = {'chat_id': f'{channel}', "parse_mode":"html", "text":final_message, "disable_web_page_preview": "true"}  # for testing
    webhook = f'https://api.telegram.org/bot{api}/sendMessage'
    r = requests.get(webhook, json = body)

def message_order_wrapper(order_message: str, id: str):
    message = f"""
👉 <b>New Trade Call</b>

{order_message}

ID : {id}
Trade Call by <b><i><a href="https://discord.gg/unitycrypto">Unity Crypto</a></i></b>
"""
    return message

def message_update_wrapper(order_message: str, id: str, profit: str):
    message = f"""
👏 <b>Result - <i>{profit}</i> Profit Trade</b> 🎉

{order_message}

ID : {id}
Trade Call by <b><i><a href="https://discord.gg/unitycrypto">Unity Crypto</a></i></b>
"""
    return message

def forward_picture(config, image_url: str):
    api = config.TELEGRAM_API
    channel = config.TELEGRAM_CHANNEL
    topic = config.TELEGRAM_PNL_TOPIC
    webhook = f'https://api.telegram.org/bot{api}/sendPhoto'
    body = {"message_thread_id": topic,
            'chat_id': f'{channel}_{topic}',
            "parse_mode":"html",
            "photo":image_url,
            "caption":""}
    r = requests.get(webhook, json = body)
