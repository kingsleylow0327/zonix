import hmac
import datetime
import json
import requests
from . import consts as c

def sign(message, secret_key):
    mac = hmac.new(bytes(secret_key, encoding='utf8'), bytes(message, encoding='utf-8'), digestmod='sha256')
    d = mac.hexdigest()
    return d

def pre_hash(timestamp, method, request_path, body):
    return str(timestamp) + str.upper(method) + request_path + body

def get_header(api_key, sign, timestamp):
    header = dict()
    header[c.CONTENT_TYPE] = c.APPLICATION_JSON
    header[c.ACCESS_KEY] = api_key
    header[c.ACCESS_SIGN] = sign
    header[c.ACCESS_TIMESTAMP] = str(timestamp)

    return header

def parse_params_to_str(params):
    url = '?'
    for key, value in params.items():
        url = url + str(key) + '=' + str(value) + '&'

    return url[0:-1]

def get_timestamp():
    now = datetime.datetime.utcnow()
    t = now.isoformat("T", "milliseconds")
    return t + "Z"

def check_coin(coin_name):
    coin_name = coin_name.upper() + "-SWAP"
    api = 'https://openapi.tapbit.com/swap/api/usdt/instruments/list'
    res = json.loads(requests.get(api).content.decode('utf-8'))["data"]
    for coin in res:
        if coin["contract_code"] == coin_name:
            return coin
    return None
