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
            config.DB_PASSWORD,
            config.POOL_SIZE)
 
    def _create_pool(self, host, port, database, user, password, size):
        try:
            pool = pooling.MySQLConnectionPool(pool_name="zonix_pool",
                pool_size=int(size),
                pool_reset_session=True,
                host=host,
                port=port,
                database=database,
                user=user,
                password=password)
            
            logger.info("DB Pool Created")
            return pool

        except Exception as e:
            logger.warning(e)
            logger.warning("DB Pool Failed")
            return None
    
    def dbcon_manager(self, sql, get_all=False):
        connection_object = self.pool.get_connection()
        row = None
        with connection_object as connection:
            with connection.cursor(dictionary=True) as cursor:
                try:
                    cursor.execute(sql)
                    row = cursor.fetchall() if get_all else cursor.fetchone()
                    connection.commit()
                except Exception as e:
                    logger.warning(sql)
                    logger.warning(e)
        if not row:
            return None
        return row
    
    def get_order_detail(self, message_id):
        sql = "select * from {} where message_id = '{}'".format(self.config.ORDER_TABLE, message_id)
        return self.dbcon_manager(sql)
    
    def get_order_msg_id(self, message_id):
        sql = """SELECT order_msg_id FROM {}
        WHERE message_id = {};
        """.format(self.config.PLAYER_ORDER,
                    message_id)
        return self.dbcon_manager(sql)

    def get_order_detail_by_order(self, order_msg_id):
        sql = """SELECT p.order_msg_id, p.status as p_status, o.* 
        FROM {} as p
        LEFT join {} as o
        ON p.message_id = o.message_id
        WHERE p.order_msg_id = {}
        """.format(self.config.PLAYER_ORDER,
                    self.config.ORDER_TABLE,
                    order_msg_id)
        return self.dbcon_manager(sql)

    def get_player_api(self, player_id):
        sql = """SELECT api_key, api_secret
        FROM {} 
        where
        player_id = '{}'
        """.format(self.config.API_TABLE, player_id)
        return self.dbcon_manager(sql, get_all=True)

    def get_followers_api(self, player_id):
        sql = """SELECT f.player_id, a.player_id as follower_id, a.api_key, a.api_secret, IF(f.player_id=follower_id,'player','') as role
        FROM {} as a
        Left JOIN {} as f
        ON f.follower_id = a.player_id
        where f.player_id = '{}'
        order by role DESC""".format(self.config.API_TABLE, self.config.FOLLOWER_TABLE, player_id)
        return self.dbcon_manager(sql, get_all=True)
    
    def set_message_player_order(self, message_id, order_id_list):
        giant_string = ", \n".join(["('{}', '{}')".format(message_id, id) for id in order_id_list])
        sql = """INSERT INTO {}(message_id, player_order)
        VALUES
        {}
        """.format(self.config.MESSAGE_PLAYER_TABLE, giant_string)
        return self.dbcon_manager(sql, get_all=True)
    
    def set_player_follower_order(self, order_id_map, main_player):
        giant_list = []
        plyer_order_list = order_id_map[main_player]
        for i in range(len(plyer_order_list)):
            for j in order_id_map:
                try:
                    giant_list.append("('{}','{}','{}',{})".format(plyer_order_list[i]["id"],
                                                                order_id_map[j][i]["id"],
                                                                j,
                                                                order_id_map[j][i]["qty"]))
                except Exception as e:
                    logger.info(e)
                    pass

        giant_string = ", \n".join(giant_list)

        sql = """INSERT INTO {}(player_order, follower_order, player_id, coin_amount)
        VALUES
        {}
        """.format(self.config.PLAYER_FOLLOWER_TABLE, giant_string)
        return self.dbcon_manager(sql, get_all=True)
    
    def get_related_oder(self, message_id):
        sql = """SELECT o.coinpair, m.message_id, m.player_order, f.follower_order, f.player_id, IF(m.player_order=f.follower_order,'player','') as role
        FROM {} as o
        LEFT JOIN {} as p
        ON p.message_id = o.message_id
        LEFT JOIN {} as m 
        ON p.order_msg_id = m.message_id
        LEFT JOIN {} as f
        ON m.player_order = f.player_order
        WHERE m.message_id = '{}'
        ORDER BY p.player_id ASC, role DESC
        """.format(self.config.ORDER_TABLE,
                   self.config.PLAYER_ORDER,
                   self.config.MESSAGE_PLAYER_TABLE,
                   self.config.PLAYER_FOLLOWER_TABLE,
                   message_id)
        return self.dbcon_manager(sql, get_all=True)
    
    def get_all_player(self):
        sql = """select * from {}
        """.format(self.config.API_TABLE)
        return self.dbcon_manager(sql, get_all=True)
    
    def get_follow_to(self, follower_id):
        sql = """SELECT * FROM {}
        where follower_id != player_id
        and
        follower_id = '{}'
        """.format(self.config.FOLLOWER_TABLE, follower_id)
        return self.dbcon_manager(sql, get_all=True)
    
    def is_admin(self, player_id):
        sql = """SELECT discord_id FROM user 
        WHERE discord_id='{}'""".format(player_id)
        ret = self.dbcon_manager(sql, get_all=True)
        return len(ret) != 0
    
    def is_admin_and_order_author(self, message_id, player_id):
        sql = """SELECT *
        FROM {} as p, user as u
        WHERE (p.message_id = '{}' AND p.player_id = '{}')
        OR (u.discord_id IN ('{}'))
        """.format(self.config.PLAYER_ORDER, message_id, player_id, player_id)
        ret = self.dbcon_manager(sql, get_all=True)
        if ret == None:
            return False
        return len(ret) != 0
    
    def update_market_out_price(self, price, message_id):
        sql = """UPDATE {}
        SET mo_price = {}
        WHERE message_id = '{}'
        """.format(self.config.ORDER_TABLE, price, message_id)
        self.dbcon_manager(sql, get_all=True)

    def close_cursor(self):
        self.cursor.close()