def get_follower_data(dbcon, result, platform):
    return_json = {}
    error_json  = {
        "non-order"     : [],
        "api-pair-fail" : []
    }
    
    if result is None:
        error_json["non-order"].append("Order Detail Not found")
        
        return_json["status_code"] = "400"
        return_json["message"]     = error_json
        
        return return_json
    
    # get api list
    api_pair_list = dbcon.get_followers_api(result["player_id"], platform)
        
    if api_pair_list == None or len(api_pair_list) == 0:
        error_json["api-pair-fail"].append("Both Trader and Follower have not set API, actual order execution skipped")
        
        return_json["status_code"] = "400"
        return_json["message"]     = error_json
        
        return return_json
    
    # Prepare the follower list which data from DB
    follower_data = [
        {
            "api_key"       : x.get("api_key"),
            "api_secret"    : x.get("api_secret"),
            "role"          : x.get("role"),
            "player_id"     : x.get("follower_id"),
            "damage_cost"   : int(x.get("damage_cost"))
        } 
        for x in api_pair_list
    ]
    
    return_json["status_code"] = "200"
    return_json["message"]     = follower_data
        
    return return_json

def coin_pair_format(coin):
    coin_pair = coin.strip().replace("/","").replace("-","").upper()
    coin_pair = coin_pair[:-4] + "-" + coin_pair[-4:]
    
    return coin_pair
