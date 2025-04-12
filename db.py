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


def get_history_records(page, size, query='', show_empty_email=False):
    """查询历史记录，支持搜索、分页和邮箱不为空筛选"""
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        offset = (page - 1) * size

        # 基础 SQL 查询
        sql = """
            SELECT id, name, website, email, phones, facebook, twitter, instagram, linkedin, whatsapp, youtube, send_count, updated_at, created_at
            FROM business_records
            WHERE 1=1
        """
        count_sql = """
            SELECT COUNT(*) as total
            FROM business_records
            WHERE 1=1
        """
        params = []
        count_params = []

        # 添加邮箱筛选条件
        if not show_empty_email:
            sql += " AND (email IS NOT NULL AND email != '')"
            count_sql += " AND (email IS NOT NULL AND email != '')"

        # 添加搜索条件
        if query:
            sql += " AND (name LIKE %s OR email LIKE %s)"
            count_sql += " AND (name LIKE %s OR email LIKE %s)"
            query_param = f"%{query}%"
            params.extend([query_param, query_param])
            count_params.extend([query_param, query_param])

        # 添加排序和分页
        sql += " ORDER BY updated_at,created_at DESC LIMIT %s OFFSET %s"
        params.extend([size, offset])

        # 执行查询
        cursor.execute(sql, params)
        records = cursor.fetchall()

        # 查询总数
        cursor.execute(count_sql, count_params)
        total = cursor.fetchone()['total']

        return records, total

    except Exception as e:
        print(f"查询历史记录失败: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return [], 0

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

def get_last_position(url):
    cnx = mysql.connector.connect(**DB_CONFIG)
    cursor = cnx.cursor()
    query = "SELECT last_position FROM last_extraction_positions WHERE url = %s"
    cursor.execute(query, (url,))
    result = cursor.fetchone()
    cursor.close()
    cnx.close()
    return result[0] if result else None

def save_last_position(url, last_position):
    cnx = mysql.connector.connect(**DB_CONFIG)
    cursor = cnx.cursor()
    query = "INSERT INTO last_extraction_positions (url, last_position) VALUES (%s, %s) ON DUPLICATE KEY UPDATE last_position = %s, timestamp = CURRENT_TIMESTAMP"
    cursor.execute(query, (url, last_position, last_position))
    cnx.commit()
    cursor.close()
    cnx.close()

def  get_facebook_non_email():
    cnx = mysql.connector.connect(**DB_CONFIG)
    cursor = cnx.cursor()
    query = "SELECT id,facebook FROM business_records WHERE facebook is not null and  email is null"
    cursor.execute(query)
    result = cursor.fetchall()
    return result
def update_business_email(business_id, email):
    """更新 business_records 表中指定 ID 的记录的邮箱"""
    try:
        cnx = get_db_connection()
        cursor = cnx.cursor()
        query = "UPDATE business_records SET email = %s WHERE id = %s"
        cursor.execute(query, (email, business_id))
        cnx.commit()
        cursor.close()
        cnx.close()
        return True
    except mysql.connector.Error as err:
        print(f"更新数据库邮箱失败: {err}")
        if err.errno == 1062:  # 1062 是 Duplicate entry 的错误代码
            delete_business_email(business_id)
            print(f"更新重复，删除: {business_id}")
        return False
def delete_business_email(business_id):
    """删除 business_records 表中指定 ID 的记录"""
    try:
        cnx = get_db_connection()
        cursor = cnx.cursor()
        query = "DELETE FROM business_records WHERE id = %s"
        cursor.execute(query, (business_id,))  # 将 business_id 放在一个元组中
        cnx.commit()
        cursor.close()
        cnx.close()
        return True
    except mysql.connector.Error as err:
        print(f"删除数据库记录失败: {err}")
        return False
if __name__ == "__main__":
    # 测试代码
    records, total = get_history_records(1, 10, "example")
    print(f"Records: {records}")
    print(f"Total: {total}")