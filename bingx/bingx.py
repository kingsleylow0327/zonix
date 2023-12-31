from hashlib import sha256
import hmac
import requests
import json
from dto.dto_bingx_order import dtoBingXOrder
from dto.dto_bingx_order_tpsl import dtoBingXOrderTPSL

APIDOMAIN = "https://open-api.bingx.com"
DEMO_API = "https://open-api-vst.bingx.com"
SERVER_TIME = "/openApi/swap/v2/server/time"
WALLET_API = "/openApi/swap/v2/user/balance"
BATCH_ORDER_API = "/openApi/swap/v2/trade/batchOrders"
MARGIN_API = "/openApi/swap/v2/trade/marginType"
LEVERAGE_API = "/openApi/swap/v2/trade/leverage"
CLOSE_ALL_ORDER_API = "/openApi/swap/v2/trade/allOpenOrders"
CLOSE_ALL_POS = "/openApi/swap/v2/trade/closeAllPositions"
ORDER = "/openApi/swap/v2/trade/order"
PENDING_ORDER = "/openApi/swap/v2/trade/openOrders"
POSITION = "/openApi/swap/v2/user/positions"
PRICE = "/openApi/swap/v2/quote/price"
ALL_ORDER = "/openApi/swap/v2/trade/allOrders"

OK_STATUS = {"code": 200, "status": "ok"}
HTTP_OK_LIST = [0, 200]

class BINGX:

    def __init__(self, api_key, api_secret) -> None:
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = requests.Session()
        pass

    def __is_error(self, json):
        return json.get("code") != None and json.get("code") not in HTTP_OK_LIST

    def __get_server_time(self):
        r = self.session.get("%s%s" % (DEMO_API, SERVER_TIME))
        if r.status_code == 200 and r.json().get("data") and r.json().get("data").get("serverTime"):
            return str(r.json().get("data").get("serverTime"))
        else:
            return None

    def __get_sign(self, payload):
        signature = hmac.new(self.api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
        return signature
    
    def __prase_param(self, params_map, time_stamp):
        sortedKeys = sorted(params_map)
        param_str = "&".join(["%s=%s" % (x, params_map[x]) for x in sortedKeys])
        param_str += "&timestamp="+time_stamp
        return param_str
    
    def __send_request(self, method, api, param_map):
        server_time = self.__get_server_time()
        if not server_time:
            return {"Timestamp error"}
        param_str = self.__prase_param(param_map, server_time)
        url = "%s%s?%s&signature=%s" % (DEMO_API, api, param_str, self.__get_sign(param_str))
        headers = {
            'X-BX-APIKEY': self.api_key,
        }
        r = self.session.request(method, url, headers=headers, data={})
        if r.json().get("code") == 200 and r.json().get("data") != None:
            return r.json().get("data")
        else:
            return r.json()
        
    def get_price(self, symbol):
        method = "GET"
        param_map = {
            "symbol": symbol,
            "recvWindow": 0
        }
        return self.__send_request(method, PRICE, param_map).get("data").get("price")
    
    def get_wallet(self):
        method = "GET"
        param_map = {
            "recvWindow": 0
        }
        return self.__send_request(method, WALLET_API, param_map).get("data").get("balance").get("availableMargin")
    
    def get_order(self, symbol, clientOrderId):
        method = "GET"
        param_map = {
            "symbol": symbol,
            "clientOrderID": clientOrderId,
            "recvWindow": 0
        }
        return self.__send_request(method, ORDER, param_map)
    
    def get_position(self, symbol):
        method = "GET"
        param_map = {
            "symbol": symbol,
            "recvWindow": 0
        }
        return self.__send_request(method, POSITION, param_map)
    
    def get_all(self, symbol):
        method = "GET"
        param_map = {
            "symbol": symbol,
            "limit": "500",
            "recvWindow": 0
        }
        return self.__send_request(method, ALL_ORDER, param_map)
    
    def get_all_pending(self, symbol):
        method = "GET"
        param_map = {
            "symbol": symbol,
            "recvWindow": 0
        }
        return self.__send_request(method, PENDING_ORDER, param_map)
    
    def place_order(self, player_order_list):
        method = "POST"
        stringify = self.__stringify_json(player_order_list)
        param_map = {
            "batchOrders": stringify
        }
        return self.__send_request(method, BATCH_ORDER_API, param_map)
    
    def close_order(self, symbol, player_order_list):
        method = "DELETE"
        stringify = self.__stringify_json(player_order_list)
        param_map = {
            "symbol": symbol.upper(),
            "clientOrderIDList": stringify,
            "recvWindow": 0
        }
        return self.__send_request(method, BATCH_ORDER_API, param_map)
    
    def close_all_order(self, symbol):
        method = "DELETE"
        param_map = {
            "symbol": symbol.upper(),
            "recvWindow": 0
        }
        return self.__send_request(method, CLOSE_ALL_ORDER_API, param_map)
    
    def close_all_pos(self, symbol):
        method = "POST"
        param_map = {
            "symbol": symbol,
            "recvWindow": 0
        }
        return self.__send_request(method, CLOSE_ALL_POS, param_map)
    
    def get_margin(self, symbol):
        method = "GET"
        param_map = {
            "symbol": symbol.upper(), #"BTC-USDT",
            "recvWindow": 0
        }
        return self.__send_request(method, MARGIN_API, param_map)
    
    def set_margin(self, symbol):
        method = "POST"
        param_map = {
            "symbol": symbol.upper(), #"BTC-USDT",
            "marginType": "CROSSED",
            "recvWindow": 0
        }
        return self.__send_request(method, MARGIN_API, param_map)
    
    def get_leverage(self, symbol):
        method = "GET"
        param_map = {
            "symbol": symbol.upper(), #"BTC-USDT",
            "recvWindow": 0
        }
        return self.__send_request(method, LEVERAGE_API, param_map)
    
    def set_leverage(self, symbol, side, leverage):
        method = "POST"
        param_map = {
            "symbol": symbol.upper(), #"BTC-USDT",
            "side": side.upper(), #"LONG",
            "leverage": leverage, #0,
            "recvWindow": 0
        }
        return self.__send_request(method, LEVERAGE_API, param_map)
    
    def set_max_leverage(self, symbol):
        leverage_detail = self.get_leverage(symbol)
        set_leverage_return = {}
        if self.__is_error(leverage_detail):
            return leverage_detail
        if leverage_detail.get("longLeverage") != leverage_detail.get("maxLongLeverage"):
            long_lev_return = self.set_leverage(symbol, "long", leverage_detail.get("maxLongLeverage"))
            if long_lev_return.get("code") != 0:
                set_leverage_return["long_error"] = long_lev_return
        if leverage_detail.get("shortLeverage") != leverage_detail.get("maxShortLeverage"):
            short_lev_return = self.set_leverage(symbol, "short", leverage_detail.get("maxShortLeverage"))
            if short_lev_return.get("code") != 0:
                set_leverage_return["short_error"] = short_lev_return
        return set_leverage_return if self.__is_error(set_leverage_return) else OK_STATUS

    def set_cross_margin(self, symbol):
        set_margin_return = {}
        margin_detail = self.get_margin(symbol)
        if self.__is_error(margin_detail):
            return margin_detail
        if margin_detail.get("marginType") != "CROSSED":
            set_margin_return = self.set_margin(symbol)
        return set_margin_return if self.__is_error(set_margin_return) else OK_STATUS
        

    def order_preset(self, symbol):
        order_preset_return = {}
        margin_return = self.set_cross_margin(symbol)
        if margin_return.get("code") != 0:
            order_preset_return["code"] = margin_return.get("code")
            order_preset_return["margin_preset_error"] = margin_return
        leverage_return = self.set_max_leverage(symbol)
        if leverage_return.get("code") != 0:
            order_preset_return["code"] = margin_return.get("code")
            order_preset_return["leverage_preset_error"] = leverage_return
        return order_preset_return if order_preset_return != {} or self.__is_error(order_preset_return) else OK_STATUS
    
    def __stringify_json(self, j):
        return json.dumps(j).replace(', \\"', ',\\"')


