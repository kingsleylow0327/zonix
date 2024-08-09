import requests as url_requests

bingx_main_url = 'http://platform:5000/bingx'

async def bingx_conn():
    response = url_requests.get(bingx_main_url)

    return response.json()

async def place_order_conn(dbcon, message_id, regex_message):
    place_order_url = bingx_main_url + '/place_order'

    json_data = {
        'dbcon'         : dbcon,
        'message_id'    : message_id,
        'regex_message' : regex_message
    }

    response = url_requests.post(place_order_url, json=json_data)

    return response.json()