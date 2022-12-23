import os

from dotenv import load_dotenv

class Config():
    
    def __init__(self) -> None:
        load_dotenv()
        self.TOKEN = os.getenv('DISCORD_TOKEN')
        self.ZODIAC_ID = os.getenv('ZODIAC_ID')
        self.RECEIVER_CHANNEL_ID = os.getenv('RECEIVER_CHANNEL_ID')
        self.DB_ADDRESS = os.getenv('DB_ADDRESS')
        self.DB_SCHEMA = os.getenv('DB_SCHEMA')
        self.DB_USERNAME = os.getenv('DB_USERNAME')
        self.DB_PASSWORD = os.getenv('DB_PASSWORD')
        self.DB_PORT = os.getenv('DB_PORT')
        self.ORDER_TABLE = os.getenv('ORDER_TABLE')
        self.API_TABLE = os.getenv('API_TABLE')
        self.FOLLOWER_TABLE = os.getenv('FOLLOWER_TABLE')
        self.BYBIT_API_KEY = os.getenv('BYBIT_API_KEY')
        self.BYBIT_API_SECRET = os.getenv('BYBIT_API_SECRET')