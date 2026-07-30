from sshtunnel import SSHTunnelForwarder
import pymysql

class DatabaseHandler:
    def __init__(self, db_host, db_user, db_password, db, db_port,
                 ssh_host, ssh_port, ssh_username, ssh_pkey):
        self.tunnel = SSHTunnelForwarder(
            (ssh_host, ssh_port),
            ssh_username=ssh_username,
            ssh_pkey=ssh_pkey,
            remote_bind_address=(db_host, db_port)
        )

        self.tunnel.start()

        self.conn = pymysql.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db,
            port=self.tunnel.local_bind_port,
            charset='utf8',
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False
        )

        self.cursor = self.conn.cursor()

    # ---------------------------------------------------------
    # 범용 쿼리 실행기 (execute_*) : 쿼리 문자열을 외부에서 받아 그대로 실행
    # ---------------------------------------------------------
    
    
    def execute_fetch_all(self, query, params=None):
        self.cursor.execute(query, params)
        return self.cursor.fetchall()
    
    def execute_fetch_one(self, query, params=None):
        self.cursor.execute(query, params)
        return self.cursor.fetchone()

    def execute_insert(self, query, params):
        self.cursor.execute(query, params)

    def execute_update(self, query, params):
        self.cursor.execute(query, params)

    def execute_delete(self, query, params):
        self.cursor.execute(query, params)

    def get_last_inserted_id(self):
        return self.cursor.lastrowid

    def close(self):
        self.cursor.close()
        self.conn.close()
        self.tunnel.stop()

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()
    