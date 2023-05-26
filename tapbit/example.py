# import swap_api as swap
import json
import logging
import datetime
import requests

def get_timestamp():
    now = datetime.datetime.now()
    t = now.isoformat("T", "milliseconds")
    return t + "Z"

time = get_timestamp()

if __name__ == '__main__':

#     api_key = ""
#     secret_key = ""

# # swap api test
#     swapAPI = swap.SwapAPI(api_key, secret_key, False)
#     # result = swapAPI.get_ticker()
#     result = swapAPI.get_accounts()

#     # result = swapAPI.order('BTC', 'fixed', 'openLong', '0.1', '38000', '100', 'limit')
#     # result = swapAPI.get_order_info('BTC-USD-SWAP', '2')

#     print(time + json.dumps(result))
#     logging.info("result:" + json.dumps(result))
    coin_name = "ETH" + "-SWAP"
    api = 'https://openapi.tapbit.com/swap/api/usdt/instruments/list'
    res = json.loads(requests.get(api).content.decode('utf-8'))["data"]
    for coin in res:
        if coin["contract_code"] == coin_name:
            print(coin)
