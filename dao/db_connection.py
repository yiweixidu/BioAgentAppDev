# dao/db_connection.py
import pymysql
from pymysql.cursors import DictCursor
from config.db_config import DB_CONFIG

def get_connection():
    return pymysql.connect(
        **DB_CONFIG,
        cursorclass=DictCursor
    )