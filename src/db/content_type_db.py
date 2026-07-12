from db.db_handler import DatabaseHandler

def get_api_content_type(db : DatabaseHandler, content_type_name):
    query = """
        SELECT * 
        FROM api_content_type 
        WHERE content_type_name = %s
    """

    return db.execute_fetch_one(query, (content_type_name,))

