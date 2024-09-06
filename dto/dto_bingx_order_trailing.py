class dtoTrailingOrder():
    
    def __init__(self, coin_pair, side, position_side, quantity, price_rate, activation_price) -> None:
        self.player_id = None
        self.message_id = None
        self.order_link_id = None
        self.entry = None
        self.stop = None
        self.coin_pair = coin_pair
        self.side = side
        self.position_side = position_side
        self.type = "TRAILING_TP_SL"
        self.quantity = quantity
        self.price_rate = price_rate
        self.activation_price = activation_price
    
    def to_json(self):
        json = {}
        json["symbol"] = self.coin_pair
        json["side"] = self.side
        json["positionSide"] = self.position_side
        json["type"] = self.type
        json["quantity"] = self.quantity
        json["priceRate"] = self.price_rate
        json["activationPrice"] = self.activation_price
        return json
    

