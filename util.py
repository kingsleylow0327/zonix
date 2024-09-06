from decimal import Decimal, ROUND_HALF_UP

MAX_CHAR = 1500 # Max is 2000, 500 char as buffer

def spilt_discord_message(message_list):
    char_count = 0
    ret_list = []
    element_str = ""
    for message in message_list:
        message = message + "\n"
        char_count += len(message)

        if char_count >= MAX_CHAR:
            ret_list.append(element_str)
            char_count = 0
            element_str = ""

        element_str += message
    
    ret_list.append(element_str)
    return ret_list

def random_forward_order_message(message, id):
    final_message = f"""
## 👉 New Trade Call

{message}

ID : {id}
"""
    return final_message

def convert_percentage_value_to_value(entry_price, price_to_convert, is_lower=False):

    if is_lower:
        result = Decimal(entry_price) * (1 - Decimal(price_to_convert) / 100)
    else:
        result = Decimal(entry_price) * (1 + Decimal(price_to_convert) / 100)
    result = result.quantize(Decimal('1.0000'), rounding=ROUND_HALF_UP)

    return float(result)