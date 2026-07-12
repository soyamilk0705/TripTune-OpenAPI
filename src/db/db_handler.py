import pymysql

class DatabaseHandler:
    def __init__(self, host, user, password, db, port):
        self.conn = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=db,
            port=port,
            charset='utf8',
            cursorclass=pymysql.cursors.DictCursor
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
        self.conn.commit()


    def execute_update(self, query, params):
        self.cursor.execute(query, params)
        self.conn.commit()

    def execute_delete(self, query, params):
        self.cursor.execute(query, params)
        self.conn.commit()


    def get_last_inserted_id(self):
        return self.cursor.lastrowid
    

    def close(self):
        self.conn.close()
    