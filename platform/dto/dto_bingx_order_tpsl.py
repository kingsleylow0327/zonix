class dtoBingXOrderTPSL():

    def __init__(self, symbol, tpsl, side, positionSide, price, quantity) -> None:
        self.symbol = symbol
        self.tpsl = tpsl
        self.side = side
        self.positionSide = positionSide
        self.price = price
        self.quantity = quantity

    def to_json(self):
        json = {}
        json["symbol"] = self.symbol
        if self.tpsl == "tp":
            json["type"] = "TAKE_PROFIT"
        else:
            json["type"] = "STOP"
        json["side"] = self.side
        json["positionSide"] = self.positionSide
        json["quantity"] = self.quantity
        json["stopPrice"] = self.price
        json["price"] = self.price
        json["workingType"] = "MARK_PRICE"
        return json