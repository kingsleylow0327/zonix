from config import Config

from mysql.connector import pooling
from logger import Logger

# Logger setup
logger_mod = Logger("DB")
logger = logger_mod.get_logger()

class ZonixDB():
    def __init__(self, config):
        self.config = config
        self.pool = self._create_pool(config.DB_ADDRESS,
            config.DB_PORT,
            config.DB_SCHEMA,
            config.DB_USERNAME,
            config.DB_PASSWORD)
 
    def _create_pool(self, host, port, database, user, password):
        try:
            pool = pooling.MySQLConnectionPool(pool_name="zonix_pool",
                pool_size=10,
                pool_reset_session=True,
                host=host,
                port=port,
                database=database,
                user=user,
                password=password)
            
            logger.info("DB Pool Created")
            return pool

        except Exception as e:
            logger.info(e)
            logger.info("DB Pool Failed")
            return None
    
    def dbcon_manager(self, sql, get_all=False):
        connection_object = self.pool.get_connection()
        row = None
        with connection_object as connection:
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute(sql)
                row = cursor.fetchall() if get_all else cursor.fetchone()
        return row
    
    def get_order_detail_uat(self, message_id):
        sql = "select * from {} where message_id = '{}'".format(self.config.ORDER_TABLE, message_id)
        return self.dbcon_manager(sql)

    def get_followers_api(self, player_id):
        sql = """SELECT f.player_id, a.player_id as follower_id, a.api_key, a.api_secret
        FROM {} as a
        Left JOIN {} as f
        ON f.follower_id = a.player_id
        where f.player_id = '{}'""".format(self.config.API_TABLE, self.config.FOLLOWER_TABLE, player_id)
        return self.dbcon_manager(sql, get_all=True)
    
    def close_cursor(self):
        self.cursor.close()

