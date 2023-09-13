import requests
import json

def h_check_price(symbol):
    api = f"https://api.bybit.com/spot/quote/v1/ticker/price?symbol={symbol.upper()}"
    r = requests.get(api)
    try:
        return json.loads(r.content).get("result").get(["price"])
    except:
        return "(error geting price from bybit)" 
