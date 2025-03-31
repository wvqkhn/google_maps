import pandas as pd
from datetime import datetime
from config import OUTPUT_DIR
import os

def save_to_csv(data):
    if not data:
        print("没有数据可保存")
        return None

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"google_maps_data_{timestamp}.csv"
    filepath = os.path.join(OUTPUT_DIR, filename)

    df = pd.DataFrame(data)
    df.to_csv(filepath, sep=';', encoding='utf-8-sig', index=False)
    print(f"数据已保存到 {filepath}")
    return filename