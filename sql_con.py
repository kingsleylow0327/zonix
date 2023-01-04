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
                connection.commit()
        return row
    
    def get_order_detail_uat(self, message_id):
        sql = "select * from {} where message_id = '{}'".format(self.config.ORDER_TABLE, message_id)
        return self.dbcon_manager(sql)

    def get_followers_api(self, player_id):
        sql = """SELECT f.player_id, a.player_id as follower_id, a.api_key, a.api_secret, IF(f.player_id=follower_id,'player','') as role
        FROM {} as a
        Left JOIN {} as f
        ON f.follower_id = a.player_id
        where f.player_id = '{}'""".format(self.config.API_TABLE, self.config.FOLLOWER_TABLE, player_id)
        return self.dbcon_manager(sql, get_all=True)
    
    def set_message_player_order(self, message_id, order_id_list):
        giant_string = ", \n".join(["('{}', '{}')".format(message_id, id) for id in order_id_list])
        sql = """INSERT INTO {}(message_id, player_order)
        VALUES
        {}
        """.format(self.config.MESSAGE_PLAYER_TABLE, giant_string)
        print(sql)
        return self.dbcon_manager(sql, get_all=True)
    
    def set_player_follower_order(self, h_map):
        giant_list = []
        for i in h_map:
            giant_list.append(", \n".join(["('{}', '{}')".format(i, id) for id in h_map[i]]))
        giant_string = ", \n".join(giant_list)

        sql = """INSERT INTO {}(player_order, follower_order)
        VALUES
        {}
        """.format(self.config.PLAYER_FOLLOWER_TABLE, giant_string)
        print(sql)
        return self.dbcon_manager(sql, get_all=True)
    
    def get_related_oder(self, message_id):
        sql = """select m.message_id, m.player_order, p.follower_order
        from {} as m left join {} as p
        ON m.player_order = p.player_order
        where m.message_id = '{}'
        """.format(self.config.MESSAGE_PLAYER_TABLE, self.config.PLAYER_FOLLOWER_TABLE, message_id)
        print(sql)
        return self.dbcon_manager(sql, get_all=True)


    def close_cursor(self):
        self.cursor.close()

