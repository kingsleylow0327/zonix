from flask import Flask, Blueprint, jsonify, request

from service.place_order_service import place_order_main

bingx = Blueprint('bingx', __name__, url_prefix='/bingx')

@bingx.route('/', methods=['GET'])
def index():
    json = {'message' : 'Hello, BingX'}

    return jsonify(json)    

@bingx.route('/place_order', methods=['POST'])
def place_order():
    # json = {'message' : 'Hello, BingX'}

    data = request.json

    regex_message   = data['regex_message']
    message_id      = data['message_id']
    dbcon           = data['dbcon']

    order = place_order_main(dbcon, message_id, regex_message)

    data['message'] = order

    return jsonify(order)  
