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
        print(f"连接数据库时发生错误: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return None  # 或者引发一个自定义异常

def save_business_data_to_db(business_data):
    """将所有商家数据保存到 MySQL 数据库，多邮箱拆分为多行，重复邮箱则更新数据"""
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # 可选：确保 email 是唯一索引（只需运行一次）
        # cursor.execute("ALTER TABLE business_records ADD UNIQUE (email)")

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
            # 没有邮箱，不做更新判断，直接插入
            cursor.execute("""
                 INSERT INTO business_records 
                 (name, website, email, phones, facebook, twitter, instagram, linkedin, whatsapp, youtube, send_count)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0)
             """, (name, website, None, phones, facebook, twitter, instagram, linkedin, whatsapp, youtube))
        else:
            for email in emails:
                cursor.execute("""
                     INSERT INTO business_records 
                     (name, website, email, phones, facebook, twitter, instagram, linkedin, whatsapp, youtube, send_count)
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0)
                     AS new
                     ON DUPLICATE KEY UPDATE
                         name = new.name,
                         website = new.website,
                         phones = new.phones,
                         facebook = new.facebook,
                         twitter = new.twitter,
                         instagram = new.instagram,
                         linkedin = new.linkedin,
                         whatsapp = new.whatsapp,
                         youtube = new.youtube
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
                SELECT id, name, website, email, phones, facebook, twitter, instagram, linkedin, whatsapp, youtube, send_count,updated_at,created_at
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
                SELECT id, name, website, email, phones, facebook, twitter, instagram, linkedin, whatsapp, youtube, send_count,updated_at, created_at
                FROM business_records
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """
            count_sql = "SELECT COUNT(*) as total FROM business_records"
            cursor.execute(sql, (size, offset))

        records = cursor.fetchall()

        if query:
            cursor.execute(count_sql, (query_param, query_param))
        else:
            cursor.execute(count_sql)
        total = cursor.fetchone()['total']

        return records, total

    except Exception as e:  # Catch a broader range of exceptions
        print(f"查询历史记录失败: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)  # Print the full traceback for debugging
        return [], 0  # Return an empty list and 0 to indicate failure

    finally:
        if cursor:
            try:
                cursor.close()
            except Exception as e:
                print(f"关闭游标失败: {e}", file=sys.stderr)
                import traceback
                traceback.print_exc(file=sys.stderr)
        if connection and connection.is_connected():
            try:
                connection.close()
            except Exception as e:
                print(f"关闭连接失败: {e}", file=sys.stderr)
                import traceback
                traceback.print_exc(file=sys.stderr)

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
                SET send_count = send_count + 1 ,
                updated_at = CURRENT_TIMESTAMP
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