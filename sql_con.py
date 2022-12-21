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
    
    def dbcon_manager(self, sql):
        connection_object = self.pool.get_connection()
        row = None
        with connection_object as connection:
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute(sql)
                row = cursor.fetchone()
        return row
    
    def get_order_detail_uat(self, message_id):
        sql = "select * from {} where message_id = {}".format(self.config.ORDER_TABLE, message_id)
        return self.dbcon_manager(sql)
    
    def close_cursor(self):
        self.cursor.close()

