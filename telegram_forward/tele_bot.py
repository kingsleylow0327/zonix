import requests

def forward_order_to_telegram(config, order_message: str, author: str, id: str):
    api = config.TELEGRAM_API
    channel = config.TELEGRAM_CHANNEL
    topic = config.TELEGRAM_TOPIC
    final_message = message_wrapper(order_message, "", id, author, "TRADE CALL")
    webhook = f'https://api.telegram.org/bot{api}/sendMessage'
    body = {"message_thread_id": topic, 'chat_id': f'{channel}_{topic}', "text":final_message}
    r = requests.get(webhook, json = body)

def forward_update_to_telegram(type: str, dbcon, config, order_id: str, update_message=""):
    player_order = dbcon.get_order_message_by_order_msg_id(order_id)
    api = config.TELEGRAM_API
    channel = config.TELEGRAM_CHANNEL
    topic = config.TELEGRAM_TOPIC
    if not player_order:
        return
    order_message = player_order.get("message")
    order_message = "\n".join(order_message.split("\n")[0:-2])

    author = player_order.get("player_name")
    if type not in ["CANCEL", "MARKET OUT"]:
        update_message = f"\n\n{update_message}\n\n"
    final_message = message_wrapper(order_message, update_message, order_id, author, type)
    final_message = final_message.replace("#", "")
    body = {"message_thread_id": topic, 'chat_id': f'{channel}_{topic}', "text":final_message}
    webhook = f'https://api.telegram.org/bot{api}/sendMessage'
    r = requests.get(webhook, json = body)

def message_wrapper(order_message: str, update_message: str, id: str, author: str, type: str):
    message=f"""
< {author} > has made {type}!
{update_message}
ID : {id}

{order_message}

*Trade call forwarded From ✨UNITY CRYPTO✨

Join our discord server to know more -> https://discord.gg/zrrnft
"""
    return message

if __name__ == "__main__":
    """curl -X POST -H 'Content-Type: application/json' \
 -d '{"message_thread_id": "1234", "chat_id": "-1001234567890_1234", "text": "This is a test message from the alert system. Do not pay attention on it"}' \
 https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage"""
    api = "7139621534:AAH7rXde3WOlR3LVzBEIb2n5z7KCPu-W08A"
    url = f'https://api.telegram.org/bot{api}/sendMessage'
    myobj = {"message_thread_id": "12", 'chat_id': '-1002061232388_12', "text":"test"}

    x = requests.post(url, json = myobj)
    print(x)