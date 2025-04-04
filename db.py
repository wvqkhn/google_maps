import mysql.connector
import sys
from mysql.connector import Error
from config import DB_CONFIG

def get_db_connection():
    """创建并返回 MySQL 数据库连接"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"连接 MySQL 失败: {e}", file=sys.stderr)
        raise

def save_business_data_to_db(business_data):
    """将所有商家数据保存到 MySQL 数据库，多邮箱拆分为多行"""
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # 创建表（如果不存在）
        # cursor.execute("""
        #     CREATE TABLE IF NOT EXISTS business_records (
        #         id INT AUTO_INCREMENT PRIMARY KEY,
        #         name VARCHAR(255),
        #         website TEXT,
        #         email VARCHAR(255),
        #         phones TEXT,
        #         facebook TEXT,
        #         twitter TEXT,
        #         instagram TEXT,
        #         linkedin TEXT,
        #         whatsapp TEXT,
        #         youtube TEXT,
        #         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        #     )
        # """)

        # 插入数据
        for business in business_data:
            name = business.get('name', '')
            website = business.get('website', '')
            emails = business.get('emails', []) if business.get('emails') else []
            phones = ', '.join(business.get('phones', [])) if business.get('phones') else ''
            facebook = business.get('facebook', '')
            twitter = business.get('twitter', '')
            instagram = business.get('instagram', '')
            linkedin = business.get('linkedin', '')
            whatsapp = business.get('whatsapp', '')
            youtube = business.get('youtube', '')

            # 如果没有邮箱，则插入一行
            if not emails:
                cursor.execute("""
                    INSERT INTO business_records 
                    (name, website, email, phones, facebook, twitter, instagram, linkedin, whatsapp, youtube)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (name, website, None, phones, facebook, twitter, instagram, linkedin, whatsapp, youtube))
            else:
                # 对于每个邮箱，插入一行
                for email in emails:
                    cursor.execute("""
                        INSERT INTO business_records 
                        (name, website, email, phones, facebook, twitter, instagram, linkedin, whatsapp, youtube)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (name, website, email, phones, facebook, twitter, instagram, linkedin, whatsapp, youtube))

        connection.commit()
        print(f"成功保存 {len(business_data)} 个商家数据到数据库", file=sys.stderr)

    except Error as e:
        print(f"保存商家数据到数据库失败: {e}", file=sys.stderr)
        raise
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()