from flask import Flask, Blueprint, jsonify, request

from service.place_order_service import place_order_service

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

    json = {'message' : 'BingX PTP'}

    return jsonify(json)

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
    # 0 : Cancel One Order
    # 1 : Cancel All Order
    cancel_type = data['type']

    json = {'message' : 'BingX Cancel Order'}

    return jsonify(json)  

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