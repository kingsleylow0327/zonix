def h_get_order_detail(dbcon, msg_id):
    ret_json = dbcon.get_order_detail_by_order(msg_id)
    if ret_json == None:
        return "This order is not recognized"
    coin_pair = ret_json["coinpair"]
    long_short = ret_json["long_short"]
    entry_list = [ret_json["entry1"], ret_json["entry2"]]
    entry_list = "\n".join([str(i) for i in entry_list if i != -1])
    tp_list = [ret_json["tp1"], ret_json["tp2"], ret_json["tp3"], ret_json["tp4"]]
    tp_list = "\n".join([str(i) for i in tp_list if i != -1])
    stop = ret_json["stop"]
    msg_format = f"""
👑 Tradecall received by Zonix Trading Bot 👑

{coin_pair}{long_short}

Entry:
{entry_list}

TP:
{tp_list}

STOP:
{stop}

**Please type `Cancel` if the above Tradecall is not the same as your posted, contact admin for more inquiry**

    """
    return msg_format