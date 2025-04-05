import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG
import sys
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
        #         send_count INT DEFAULT 0,  -- 新增发送次数列，默认为 0
        #         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        #     )
        # """)

        # 检查是否需要添加 send_count 列（兼容已有表）
        # cursor.execute("SHOW COLUMNS FROM business_records LIKE 'send_count'")
        # if not cursor.fetchone():
        #     cursor.execute("ALTER TABLE business_records ADD COLUMN send_count INT DEFAULT 0")

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

            if not emails:
                cursor.execute("""
                    INSERT INTO business_records 
                    (name, website, email, phones, facebook, twitter, instagram, linkedin, whatsapp, youtube, send_count)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (name, website, None, phones, facebook, twitter, instagram, linkedin, whatsapp, youtube, 0))
            else:
                for email in emails:
                    cursor.execute("""
                        INSERT INTO business_records 
                        (name, website, email, phones, facebook, twitter, instagram, linkedin, whatsapp, youtube, send_count)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (name, website, email, phones, facebook, twitter, instagram, linkedin, whatsapp, youtube, 0))

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

def get_history_records(page, size, query=''):
    """查询历史记录，支持搜索和分页"""
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        offset = (page - 1) * size

        if query:
            sql = """
                SELECT id, name, website, email, phones, facebook, twitter, instagram, linkedin, whatsapp, youtube, send_count, created_at 
                FROM business_records 
                WHERE name LIKE %s OR email LIKE %s 
                ORDER BY created_at DESC 
                LIMIT %s OFFSET %s
            """
            count_sql = """
                SELECT COUNT(*) as total 
                FROM business_records 
                WHERE name LIKE %s OR email LIKE %s
            """
            query_param = f"%{query}%"
            cursor.execute(sql, (query_param, query_param, size, offset))
        else:
            sql = """
                SELECT id, name, website, email, phones, facebook, twitter, instagram, linkedin, whatsapp, youtube, send_count, created_at 
                FROM business_records 
                ORDER BY created_at DESC 
                LIMIT %s OFFSET %s
            """
            count_sql = "SELECT COUNT(*) as total FROM business_records"
            cursor.execute(sql, (size, offset))

        records = cursor.fetchall()

        cursor.execute(count_sql, (query_param, query_param) if query else None)
        total = cursor.fetchone()['total']

        return records, total

    except Error as e:
        print(f"查询历史记录失败: {e}", file=sys.stderr)
        raise
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

def update_send_count(emails):
    """更新指定邮箱的发送次数"""
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        for email in emails:
            cursor.execute("""
                UPDATE business_records 
                SET send_count = send_count + 1 
                WHERE email = %s
            """, (email,))

        connection.commit()
        print(f"成功更新 {len(emails)} 个邮箱的发送次数", file=sys.stderr)

    except Error as e:
        print(f"更新发送次数失败: {e}", file=sys.stderr)
        raise
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

if __name__ == "__main__":
    # 测试代码
    records, total = get_history_records(1, 10, "example")
    print(f"Records: {records}")
    print(f"Total: {total}")