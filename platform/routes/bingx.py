from flask import Flask, Blueprint, jsonify, request

from service.place_order_service import place_order_service
from service.cancel_order_service import cancel_order_service, cancel_all_service
from service.ptp_service import ptp_service

bingx = Blueprint('bingx', __name__, url_prefix='/bingx')

@bingx.route('/', methods=['GET'])
def index():
    json = {'message' : 'Hello, BingX'}

    return jsonify(json)    

@bingx.route('/place_order', methods=['POST'])
def place_order():
    data = request.json

    regex_data      = data['regex_data']
    follower_data   = data['follower_data']

    order = place_order_service(regex_data, follower_data)

    return jsonify(order)  

@bingx.route('/strategy_place_order', methods=['POST'])
def strategy_place_order():
    data = request.json

    json = {'message' : 'BingX Strategy Place Order'}

    return jsonify(json)

@bingx.route('/take_profit', methods=['POST'])
def take_profit():
    data = request.json

    json = {'message' : 'BingX TP'}

    return jsonify(json)

@bingx.route('/partial_take_profit', methods=['POST'])
def partial_take_profit():
    data = request.json
    
    follower_data   = data['follower_data']
    coin_pair       = data['coin_pair']
    result          = data['result']
    coin_info       = data['coin_info']
    
    response = ptp_service(follower_data, coin_pair, coin_info, result)

    return jsonify(response)

@bingx.route('/safety_pin', methods=['POST'])
def safety_pin():
    data = request.json

    json = {'message' : 'BingX SP'}

    return jsonify(json)

@bingx.route('/order_details', methods=['GET'])
def order_details():
    data = request.json

    json = {'message' : 'BingX get the order details'}

    return jsonify(json)  

@bingx.route('/cancel_order', methods=['POST'])
def cancel_order():
    data = request.json

    # Type
    # 0 : Cancel Part of Position / Order
    # 1 : Cancel All Order
    cancel_type = data['type']
    
    if (cancel_type == 0) :
        follower_data   = data['follower_data']
        coin_pair       = data['coin_pair']
        result          = data['result']
        is_not_tp       = data['is_not_tp']
        
        response = cancel_order_service(follower_data, coin_pair, is_not_tp, result)
    
    elif (cancel_type == 1) :
        follower_data   = data['follower_data']
        coin            = data['coin']
        
        response = cancel_all_service(follower_data, coin)

    return jsonify(response)  

@bingx.route('/test_api', methods=['GET'])
def test_api():
    data = request.json

    json = {'message' : 'BingX Test API'}

    return jsonify(json)

@bingx.route('/monthly_close_order', methods=['GET'])
def monthly_close_order():
    data = request.json

    json = {'message' : 'BingX Close Order Monthly'}

    return jsonify(json)    