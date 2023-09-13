def h_monthly_close_by_order_id(db, last_month, this_month):
    return db.get_order_by_ref_id(last_month, this_month)