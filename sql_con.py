from mysql.connector import pooling

class ZonixDB():
    def __init__(self, config):
        self.config = config
        self.pool = self._create_pool(config.DB_ADDRESS,
            config.DB_PORT,
            config.DB_SCHEMA,
            config.DB_USERNAME,
            config.DB_PASSWORD)
        self.cursor = self.create_cursor()
 
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

            connection_object = pool.get_connection()
            if not connection_object.is_connected():
                print("DB Not connceted")
                return None
            
            print("DB Connection Established")
            return connection_object

        except Exception as e:
            print(e)
            print("DB Connection Failed")
            return None

    def create_cursor(self, buffer=False):
        # if need to iterate using cursor, set buffer to true
        # https://docs.oracle.com/cd/E17952_01/connector-python-en/connector-python-tutorial-cursorbuffered.html
        if not self.pool.is_connected():
            print("DB Not connceted")
            return None

        self.cursor = self.pool.cursor(dictionary=True, buffered=buffer)
        return self.cursor
    
    def close_cursor(self):
        self.cursor.close()
    
    def get_order_detail_uat(self, message_id):
        sql = "select * from {} where message_id = {}".format(self.config.ORDER_TABLE, message_id)
        try:
            self.cursor.execute(sql)
            return self.cursor.fetchone()
        except Exception as e:
            print(e)
            print(sql)
            return None
