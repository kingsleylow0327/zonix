import requests
import json

def h_check_price(symbol):
    api = f"https://api.bybit.com/spot/quote/v1/ticker/price?symbol={symbol.upper()}"
    r = requests.get(api)
    return json.loads(r.content)["result"]["price"]
