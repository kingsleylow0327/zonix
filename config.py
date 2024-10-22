import os

from dotenv import load_dotenv

class Config():
    
    def __init__(self) -> None:
        load_dotenv()
        self.TOKEN = os.getenv('DISCORD_TOKEN')
        self.ZODIAC_ID = os.getenv('ZODIAC_ID')
        self.ZONIX_ID = os.getenv('ZONIX_ID')
        self.SENDER_CHANNEL_ID = os.getenv('SENDER_CHANNEL_ID')
        self.RECEIVER_CHANNEL_ID = os.getenv('RECEIVER_CHANNEL_ID')
        self.COMMAND_CHANNEL_ID = os.getenv('COMMAND_CHANNEL_ID')
        self.DB_ADDRESS = os.getenv('DB_ADDRESS')
        self.DB_SCHEMA = os.getenv('DB_SCHEMA')
        self.DB_USERNAME = os.getenv('DB_USERNAME')
        self.DB_PASSWORD = os.getenv('DB_PASSWORD')
        self.DB_PORT = os.getenv('DB_PORT')
        self.PLAYER_ORDER = os.getenv('PLAYER_ORDER')
        self.ORDER_TABLE = os.getenv('ORDER_TABLE')
        self.API_TABLE = os.getenv('API_TABLE')
        self.FOLLOWER_TABLE = os.getenv('FOLLOWER_TABLE')
        self.BYBIT_API_KEY = os.getenv('BYBIT_API_KEY')
        self.BYBIT_API_SECRET = os.getenv('BYBIT_API_SECRET')
        self.MESSAGE_PLAYER_TABLE=os.getenv('MESSAGE_PLAYER_TABLE')
        self.PLAYER_FOLLOWER_TABLE=os.getenv('PLAYER_FOLLOWER_TABLE')
        self.SERVER_IP=os.getenv('SERVER_IP')
        self.POOL_SIZE=os.getenv('POOL_SIZE')
        self.IS_TEST=os.getenv('IS_TEST')