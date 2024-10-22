class dtoOrder():
    
    def __init__(self, target_price, symbol, side, quantity, take_profit, stop_loss, leverage) -> None:
        self.target_price = target_price
        self.symbol = self._strip_coin(symbol)
        self.side = self._change_side(side)
        self.quantity = quantity
        self.take_profit = take_profit
        self.stop_loss = stop_loss
        self.leverage = leverage
        self.order_link_id = ""
    
    def _change_side(self, side):
        return "Sell" if side.upper() == "SHORT" or side.upper() == "SELL" else "Buy"
    
    def _strip_coin(self, symbol):
        return symbol.strip().replace("/","").upper()
