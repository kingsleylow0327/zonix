import requests

def forward_to_telegram(api: str , channel: str, message: str, author: str):
    message = message_wrapper(message, author)
    webhook = f"https://api.telegram.org/bot{api}/sendMessage?chat_id=@{channel}&text={message}"
    r = requests.get(webhook)

def message_wrapper(message: str, author: str):
    message_header=f"< {author} > has made a TRADE CALL! \n\n"
    message_footer="*Trade call forwarded From ✨ZONIX✨"

    return f"{message_header}{message}\n{message_footer}"