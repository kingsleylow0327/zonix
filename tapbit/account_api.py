from .client import Client
from .consts import *


class AccountAPI(Client):

    def __init__(self, api_key, api_secret_key, use_server_time=False):
        Client.__init__(self, api_key, api_secret_key, use_server_time)

    # get all currencies list
    def get_currencies(self):
        return self._request_without_params(GET, CURRENCY_INFO)

    # get deposit address list
    def get_deposit_address(self, asset):
        params = {"asset": asset}
        return self._request_with_params(GET, DEPOSIT_ADDRESS, params)

