
# http header
API_URL = 'https://openapi.tapbit.com/swap/'
CONTENT_TYPE = 'Content-Type'
ACCESS_KEY = 'ACCESS-KEY'
ACCESS_SIGN = 'ACCESS-SIGN'
ACCESS_TIMESTAMP = 'ACCESS-TIMESTAMP'

ACEEPT = 'Accept'
COOKIE = 'Cookie'
LOCALE = 'Locale='

APPLICATION_JSON = 'application/json'

GET = "GET"
POST = "POST"
DELETE = "DELETE"

SERVER_TIMESTAMP_URL = '/api/v1/spot/time'

# account
CURRENCY_INFO = '/api/capital/v1/account/currency/list'
DEPOSIT_ADDRESS = '/api/capital/v1/deposit/address/list'

# spot
SPOT_ACCOUNT_INFO = '/api/v1/spot/account/list'
SPOT_COIN_ACCOUNT_INFO = '/api/v1/spot/account/one'
SPOT_ORDER_INFO = '/api/v1/spot/order_info'
SPOT_ORDER = '/api/v1/spot/order'
SPOT_CANCEL_ORDER = '/api/v1/spot/cancel_order'
SPOT_ORDERS = '/api/v1/spot/batch_order'
SPOT_REVOKE_ORDERS = '/api/v1/spot/batch_cancel_order'
SPOT_COIN_INFO = '/api/spot/instruments/trade_pair_list'
SPOT_DEPTH = '/api/spot/instruments/depth'
SPOT_TICKER = '/api/spot/instruments/ticker_list'
SPOT_SPECIFIC_TICKER = '/api/spot/instruments/ticker_one'
SPOT_KLINE = '/api/spot/instruments/candles'
SPOT_DEAL = '/api/spot/instruments/trade_list'
SPOT_ORDERS_LIST = '/api/v1/spot/open_order_list'
SPOT_ORDERS_PENDING = '/api/v1/spot/open_order_list'

# swap usdt
SWAP_ACCOUNT = '/api/v1/usdt/account'
SWAP_ORDER = '/api/v1/usdt/order'
SWAP_ORDER_INFO = '/api/v1/usdt/order_info'
SWAP_TICKETS = '/api/usdt/instruments/ticker_list'
SWAP_CANCEL = '/api/v1/usdt/cancel_order'
SWAP_TPSL = '/api/v1/usdt/plan_close_order'
SWAP_POSITION = '/api/v1/usdt/position_list'
SWAP_ORDER_LIST="/api/v1/usdt/open_order_list"