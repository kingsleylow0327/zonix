MAX_CHAR = 1500 # Max is 2000, 500 char as buffer

def spilt_discord_message(message_list, dot=False):
    char_count = 0
    ret_list = []
    element_str = ""
    for message in message_list:
        if dot == True:
            message = "• " + message + "\n"
        else:
            message = message + "\n"
            
        char_count += len(message)

        if char_count >= MAX_CHAR:
            ret_list.append(element_str)
            char_count = 0
            element_str = ""

        element_str += message
    
    ret_list.append(element_str)
    return ret_list