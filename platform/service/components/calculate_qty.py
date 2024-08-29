maximum_wallet  = 3000
minimum_wallet  = 300

def calculate_qty(wallet, entry_price, sl, percentage): 
    wallet      = float(wallet)
    entry_price = float(entry_price)
    sl          = float(sl)
    percentage  = float(percentage)  
    
    if wallet > maximum_wallet:
        wallet = maximum_wallet
    
    price_diff = entry_price - sl
    if price_diff < 0:
        price_diff *= -1
    
    order_margin = wallet * percentage/100
    qty = order_margin/price_diff 
    return qty