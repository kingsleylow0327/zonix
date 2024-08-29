from flask import Flask, Blueprint, jsonify, request

from service.place_order_service import place_order_service
from service.cancel_order_service import cancel_order_service, cancel_all_service
from service.ptp_service import ptp_service
from service.sp_service import sp_service
from service.strategy_order_service import strategy_order_service

bingx = Blueprint('bingx', __name__, url_prefix='/bingx')

@bingx.route('/', methods=['GET']) # done
def index():
    json = {'message' : 'Hello, BingX'}

    return jsonify(json)    

@bingx.route('/place_order', methods=['POST']) # done
def place_order():
    data = request.json

    follower_data   = data['follower_data']
    coin_pair       = data['coin_pair']
    result          = data['result']
    entry           = data['entry']
    tp              = data['tp']
    

    response = place_order_service(follower_data, coin_pair, result, entry, tp)

    return jsonify(response)  

@bingx.route('/strategy_place_order', methods=['POST']) # done
def strategy_place_order():
    data = request.json

    regex_data      = data['regex_data']
    follower_data   = data['follower_data']

    response = strategy_order_service(regex_data, follower_data)

    return jsonify(response)  

@bingx.route('/partial_take_profit', methods=['POST']) # done
def partial_take_profit():
    data = request.json
    
    follower_data   = data['follower_data']
    coin_pair       = data['coin_pair']
    result          = data['result']
    coin_info       = data['coin_info']
    
    response = ptp_service(follower_data, coin_pair, coin_info, result)

    return jsonify(response)

@bingx.route('/safety_pin', methods=['POST']) #done
def safety_pin():
    data = request.json
    
    follower_data   = data['follower_data']
    coin_pair       = data['coin_pair']
    result          = data['result']

    response = sp_service(follower_data, coin_pair, result)

    return jsonify(response)

@bingx.route('/cancel_order', methods=['POST']) # done
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