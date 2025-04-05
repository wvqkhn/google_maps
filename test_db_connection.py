import mysql.connector
from mysql.connector import Error
import logging
from config import DB_CONFIG
# 日志配置
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')



def test_connection():
    logging.info("Starting test of database connection...")
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            logging.info("✅ Successfully connected to the database!")
            db_Info = connection.get_server_info()
            logging.info(f"MySQL Server version: {db_Info}")

            cursor = connection.cursor()
            cursor.execute("SELECT DATABASE();")
            record = cursor.fetchone()
            logging.info(f"Connected to database: {record}")

    except Error as e:
        logging.error("❌ Error while connecting to MySQL:")
        logging.exception(e)

    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            logging.info("MySQL connection is closed.")

if __name__ == "__main__":
    test_connection()
