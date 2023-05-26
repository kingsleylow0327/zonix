from .client import Client
from .consts import *

class SpotAPI(Client):

    def __init__(self, api_key, api_secret_key, use_server_time=False):
        Client.__init__(self, api_key, api_secret_key, use_server_time)

    # query spot account info
    def get_account_info(self):
        return self._request_without_params(GET, SPOT_ACCOUNT_INFO)

    # query specific coin account info
    def get_coin_account_info(self, asset):
        params = {'asset': asset}
        return self._request_with_params(GET, SPOT_COIN_ACCOUNT_INFO, params)

    # order
    def order(self, instrument_id, price, quantity, direction):
        params = {'instrument_id': instrument_id, 'price': price, 'quantity': quantity, 'direction': direction}
        return self._request_with_params(POST, SPOT_ORDER, params)

    # cancel order
    def cancel_order(self, order_id):
        params = {'order_id': order_id}
        return self._request_with_params(POST, SPOT_CANCEL_ORDER, params)

    # batch orders
    def batch_orders(self, params):
        return self._request_with_params(POST, SPOT_ORDERS, params)

    # cancel orders
    def revoke_orders(self, params):
        return self._request_with_params(POST, SPOT_REVOKE_ORDERS, params)

    # query orders list
    def get_orders_list(self, instrument_id, state, after='', before='', limit=''):
        params = {'instrument_id': instrument_id, 'state': state}
        if after:
            params['after'] = after
        if before:
            params['before'] = before
        if limit:
            params['limit'] = limit
        return self._request_with_params(GET, SPOT_ORDERS_LIST, params)

    # query order info
    def get_order_info(self, order_id):
        params = {'order_id': order_id}
        return self._request_with_params(GET, SPOT_ORDER_INFO, params)

    def get_orders_pending(self, instrument_id, latestOrderId='', limit=''):
        params = {'instrument_id': instrument_id}
        if latestOrderId:
            params['latestOrderId'] = latestOrderId
        if limit:
            params['limit'] = limit
        return self._request_with_params(GET, SPOT_ORDERS_PENDING, params)

    # query spot coin info
    def get_coin_info(self):
        return self._request_without_params(GET, SPOT_COIN_INFO)

    # query depth
    def get_depth(self, instrument_id, depth):
        params = {"instrument_id": instrument_id, "depth": depth}
        return self._request_with_params(GET, SPOT_DEPTH, params)

    # query ticker info
    def get_ticker(self):
        return self._request_without_params(GET, SPOT_TICKER)

    # query specific ticker
    def get_specific_ticker(self, instrument_id):
        params = {"instrument_id": instrument_id}
        return self._request_with_params(GET, SPOT_SPECIFIC_TICKER, params)

    def get_deal(self, instrument_id):
        params = {"instrument_id": instrument_id}
        return self._request_with_params(GET, SPOT_DEAL, params)

    # query k-line info
    def get_kline(self, instrument_id, period, start_time='', end_time=''):
        params = {"instrument_id": instrument_id, "period": period}
        if start_time:
            params['start_time'] = start_time
        if end_time:
            params['end_time'] = end_time

        # 按时间倒叙 即由结束时间到开始时间
        return self._request_with_params(GET, SPOT_KLINE, params)

        # 按时间正序 即由开始时间到结束时间
        # data = self._request_with_params(GET, SPOT_KLINE, params)
        # return list(reversed(data))
