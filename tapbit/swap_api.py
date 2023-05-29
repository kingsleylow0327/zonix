from .client import Client
from .consts import *


class SwapAPI(Client):

    def __init__(self, api_key, api_secret_key, use_server_time=False):
        Client.__init__(self, api_key, api_secret_key, use_server_time)

    def get_accounts(self):
        return self._request_without_params(GET, SWAP_ACCOUNT)

    def order(self, instrument_id, margin_mode, direction, quantity, order_price, leverage, order_type):
        params = {'instrument_id': instrument_id, 'margin_mode': margin_mode, 'direction': direction, 'quantity': quantity,
                  'order_price': order_price, "leverage": leverage, "order_type": order_type}
        return self._request_with_params(POST, SWAP_ORDER, params)
    
    def tpsl(self, instrument_id, plan_type, order_type, quantity, order_price, trigger_price, direction):
        params = {'instrument_id': instrument_id, 'plan_type': plan_type, 'order_type': order_type, 'quantity': quantity,
                  'order_price': order_price, 'trigger_price': trigger_price, "direction": direction}
        return self._request_with_params(POST, SWAP_TPSL, params)

    def get_order_info(self, instrument_id, order_id='', client_oid=''):
        return self._request_without_params(GET, SWAP_ORDER_INFO + '/' + str(instrument_id) + '/' + str(order_id))
    
    def get_order_list(self, instrument_id):
        params = {'instrument_id': instrument_id}
        return self._request_with_params(GET, SWAP_ORDER_LIST, params)

    def cancel(self, order_id):
        params = {'order_id': order_id}
        return self._request_with_params(POST, SWAP_CANCEL, params)
    
    def get_ticker(self):
        return self._request_without_params(GET, SWAP_TICKETS)
    
    def get_wallet(self):
        return float(self.get_accounts()["data"]["available_balance"])
    
    def place_tpsl(self, instrument_id, tp, sl, quantity, direction):
        self.tpsl(self, instrument_id, "takeProfit", "planLimit", quantity, tp, tp, direction)
        self.tpsl(self, instrument_id, "stopLoss", "planMarket", '', quantity, sl, direction)
    
    def get_position(self, coin):
        params = {'instrument_id': coin.upper()}
        return self._request_with_params(GET, SWAP_POSITION, params)
