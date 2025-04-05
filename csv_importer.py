import os
import sys
import csv
import pandas as pd
import logging
from config import OUTPUT_DIR
from db import save_business_data_to_db

# 设置日志配置
logging.basicConfig(level=logging.INFO)

def clean_emails(raw):
    if not raw:
        logging.debug("No emails found.")
        return []
    # 如果是字符串并且包含逗号，就按逗号分隔
    if isinstance(raw, str):
        # 直接按逗号分隔并去除空白字符
        emails = [email.strip() for email in raw.split(",") if email.strip()]
        if not emails:
            logging.debug(f"No valid emails found in raw data: {raw}")
        return emails
    # 如果已经是列表，直接返回
    if isinstance(raw, list):
        return [email.strip() for email in raw if email.strip()]
    return []

def load_csv_data(file_path):
    valid_data = []
    with open(file_path, 'r', encoding='utf-8-sig') as f:  # 尝试 utf-8-sig 编码
        reader = csv.DictReader(f)
        logging.info(f"Columns in {file_path}: {reader.fieldnames}")  # 打印列名
        reader.fieldnames = [str(field).strip() for field in reader.fieldnames if str(field).strip().lower() != 'nan']
        for row in reader:
            emails_raw = row.get("emails", "") or row.get("Emails", "")
            logging.debug(f"Raw emails for row {row}: {emails_raw}")  # 打印邮件字段
            emails = clean_emails(emails_raw)
            if not emails:
                logging.debug(f"No emails found for row {row}")
                continue
            for email in emails:
                business = {
                    'name': row.get('name', '') or row.get('Name', ''),
                    'website': row.get('website', '') or row.get('Website', ''),
                    'phones': clean_emails(row.get('phones', '') or row.get('Phones', '')),
                    'emails': [email],
                    'facebook': row.get('facebook', '') or row.get('Facebook', ''),
                    'twitter': row.get('twitter', '') or row.get('Twitter', ''),
                    'instagram': row.get('instagram', '') or row.get('Instagram', ''),
                    'linkedin': row.get('linkedin', '') or row.get('LinkedIn', ''),
                    'whatsapp': row.get('whatsapp', '') or row.get('WhatsApp', ''),
                    'youtube': row.get('youtube', '') or row.get('YouTube', ''),
                }
                valid_data.append(business)
    return valid_data

def load_xlsx_data(file_path):
    valid_data = []
    df = pd.read_excel(file_path, dtype=str)
    logging.info(f"Columns in {file_path}: {df.columns.tolist()}")  # 打印列名
    df.columns = [str(col).strip() for col in df.columns if str(col).strip().lower() != 'nan']
    df.fillna('', inplace=True)
    for _, row in df.iterrows():
        row_dict = row.to_dict()
        emails = clean_emails(row_dict.get('emails', '') or row_dict.get('Emails', ''))
        if not emails:
            logging.debug(f"No emails found for row {row_dict}")
            continue
        for email in emails:
            business = {
                'name': row_dict.get('name', '') or row_dict.get('Name', ''),
                'website': row_dict.get('website', '') or row_dict.get('Website', ''),
                'phones': clean_emails(row_dict.get('phones', '') or row_dict.get('Phones', '')),
                'emails': [email],
                'facebook': row_dict.get('facebook', '') or row_dict.get('Facebook', ''),
                'twitter': row_dict.get('twitter', '') or row_dict.get('Twitter', ''),
                'instagram': row_dict.get('instagram', '') or row_dict.get('Instagram', ''),
                'linkedin': row_dict.get('linkedin', '') or row_dict.get('LinkedIn', ''),
                'whatsapp': row_dict.get('whatsapp', '') or row_dict.get('WhatsApp', ''),
                'youtube': row_dict.get('youtube', '') or row_dict.get('YouTube', ''),
            }
            valid_data.append(business)
    return valid_data

def import_csv_and_xlsx_to_db():
    if not os.path.exists(OUTPUT_DIR):
        logging.error(f"Output directory {OUTPUT_DIR} does not exist.")
        return

    files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.csv') or f.endswith('.xlsx')]
    if not files:
        logging.info("No CSV or XLSX files found.")
        return

    # 打印所有文件列表
    logging.info("Found the following files:")
    for file in files:
        logging.info(f" - {file}")

    total_imported = 0

    for file_name in files:
        try:
            path = os.path.join(OUTPUT_DIR, file_name)
            logging.info(f"begin handle in {file_name}")
            if file_name.endswith('.csv'):
                data = load_csv_data(path)
            else:
                data = load_xlsx_data(path)

            if data:
                save_business_data_to_db(data)
                logging.info(f"Imported {len(data)} valid records from {file_name}")
                total_imported += len(data)
            else:
                logging.info(f"No valid data (with emails) found in {file_name}")
        except Exception as e:
            logging.error(f"Failed to import files: {e}", exc_info=True)

    logging.info(f"Total records imported: {total_imported}")

if __name__ == "__main__":
    import_csv_and_xlsx_to_db()
