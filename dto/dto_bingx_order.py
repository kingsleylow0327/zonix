import json


class dtoBingXOrder():

    def __init__(self, symbol, type, side, positionSide, price, quantity, takeProfit, tp_quan, stopLoss, sl_quant, clientOrderID=None, trailing_stop_price=None, trailing_stop_percentage=None) -> None:
        self.symbol = symbol
        self.type = type
        self.side = side
        self.positionSide = positionSide
        self.price = price
        self.quantity = quantity
        self.takeProfit = self.set_tp(takeProfit, tp_quan)
        self.stopLoss = self.set_sl(stopLoss, sl_quant)
        self.clientOrderID = clientOrderID
        self.trailing_stop_price = trailing_stop_price
        self.trailing_stop_percentage = trailing_stop_percentage

    def set_tp(self, tp, quantity):
        if tp == None:
            return None
        json_string = json.dumps({
            "type": "TAKE_PROFIT_MARKET",
            "quantity": quantity,
            "stopPrice": tp,
            "price": tp,
            "workingType": "MARK_PRICE"
        })
        return json_string

    def set_sl(self, sl, quantity):
        if sl == None:
            return None
        json_string = json.dumps({
            "type": "STOP_MARKET",
            "quantity": quantity,
            "stopPrice": sl,
            "price": sl,
            "workingType": "MARK_PRICE"
        })
        return json_string

    def to_json(self):
        json = {}
        json["symbol"] = self.symbol
        json["type"] = self.type
        json["side"] = self.side
        json["positionSide"] = self.positionSide
        if self.type == "LIMIT":
            json["price"] = self.price
        json["quantity"] = self.quantity
        json["takeProfit"] = self.takeProfit
        json["stopLoss"] = self.stopLoss
        if self.clientOrderID != None:
            json["clientOrderID"] = self.clientOrderID
        return json