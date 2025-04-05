import os
import sys
import csv
import ast
import pandas as pd
from config import OUTPUT_DIR
from db import save_business_data_to_db


def clean_emails(raw):
    if not isinstance(raw, (str, list)):
        return []
    if isinstance(raw, str):
        try:
            parsed = ast.literal_eval(raw)
            if isinstance(parsed, list):
                return [e.strip() for e in parsed if e.strip()]
            return [e.strip() for e in raw.split(",") if e.strip()]
        except Exception:
            return [e.strip() for e in raw.split(",") if e.strip()]
    return [e.strip() for e in raw if e.strip()]


def load_csv_data(file_path):
    valid_data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        reader.fieldnames = [str(field).strip() for field in reader.fieldnames if str(field).strip().lower() != 'nan']
        for row in reader:
            emails_raw = row.get("emails", "") or row.get("Emails", "")
            emails = clean_emails(emails_raw)
            if not emails:
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
    df.columns = [str(col).strip() for col in df.columns if str(col).strip().lower() != 'nan']
    df.fillna('', inplace=True)
    for _, row in df.iterrows():
        row_dict = row.to_dict()
        emails = clean_emails(row_dict.get('emails', '') or row_dict.get('Emails', ''))
        if not emails:
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
        print(f"[ERROR] Output directory {OUTPUT_DIR} does not exist.")
        return

    files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.csv') or f.endswith('.xlsx')]
    if not files:
        print("[INFO] No CSV or XLSX files found.")
        return

    total_imported = 0
    try:
        for file_name in files:
            path = os.path.join(OUTPUT_DIR, file_name)
            if file_name.endswith('.csv'):
                data = load_csv_data(path)
            else:
                data = load_xlsx_data(path)

            if data:
                save_business_data_to_db(data)
                print(f"[INFO] Imported {len(data)} valid records from {file_name}")
                total_imported += len(data)
            else:
                print(f"[INFO] No valid data (with emails) found in {file_name}")
    except Exception as e:
        print(f"[ERROR] Failed to import files: {e}", file=sys.stderr)

    print(f"[DONE] Total records imported: {total_imported}")


if __name__ == "__main__":
    import_csv_and_xlsx_to_db()
