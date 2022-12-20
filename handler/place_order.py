import sql_con
import bybit_con

def place_order(dbcon, message_id):
    result = dbcon.get_order_detail_uat(message_id)
    print(result)
    pass