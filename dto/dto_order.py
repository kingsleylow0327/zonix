class dtoOrder():
    
    def __init__(self, target_price, symbol, side, quantity, take_profit, stop_loss) -> None:
        self.target_price = target_price
        self.symbol = symbol
        self.side = side
        self.quantity = quantity
        self.take_profit = take_profit
        self.stop_loss = stop_loss