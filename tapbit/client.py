import requests
import json
from . import consts as c, utils, exceptions
import logging

class Client(object):

    def __init__(self, api_key, api_secret_key, use_server_time=False):

        self.API_KEY = api_key
        self.API_SECRET_KEY = api_secret_key
        self.use_server_time = use_server_time

    def _request(self, method, request_path, params):
        if method == c.GET:
            request_path = request_path + utils.parse_params_to_str(params)
        # url
        url = c.API_URL + request_path

        # 获取本地时间
        timestamp = utils.get_timestamp()
        # print(timestamp)

        # sign & header
        if self.use_server_time:
            # 获取服务器时间接口
            timestamp = self._get_timestamp()
        # print(timestamp)

        body = json.dumps(params) if method == c.POST else ""
        sign = utils.sign(utils.pre_hash(timestamp, method, request_path, str(body)), self.API_SECRET_KEY)
        print(utils.pre_hash(timestamp, method, request_path, str(body)))
        header = utils.get_header(self.API_KEY, sign, timestamp)
        # print(timestamp)

        print("url:", url)
        logging.info("url:" + '"' + url + '"')
        # print("headers:", header)
        # logging.info("headers:" + str(header))
        print("body:", body)
        logging.info("body:" + body)

        # send request
        response = None
        # f = {"http": "http://127.0.0.1:1087", "https": "http://127.0.0.1:1087"}
        if method == c.GET:

            response = requests.get(url, headers=header)
        elif method == c.POST:
            response = requests.post(url, data=body, headers=header)
        elif method == c.DELETE:
            response = requests.delete(url, headers=header)

        # exception handle
        if not str(response.status_code).startswith('2'):
            raise exceptions.APIException(response)
        try:
            return response.json()
        except ValueError:
            raise exceptions.RequestException('Invalid Response: %s' % response.text)

    def _request_without_params(self, method, request_path):
        return self._request(method, request_path, {})

    def _request_with_params(self, method, request_path, params):
        return self._request(method, request_path, params)

    def _get_timestamp(self):
        url = c.API_URL + c.SERVER_TIMESTAMP_URL
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()['iso']
        else:
            return ""
