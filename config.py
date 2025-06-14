import os

# 编码设置
OUTPUT_ENCODING = 'utf-8'
ERRORS = 'replace'

# Flask 配置
SECRET_KEY = 'your-secret-key'  # 请替换为安全的密钥
CORS_ALLOWED_ORIGINS = "*"
PASSWORD='admin'
# 文件路径
OUTPUT_DIR = 'output'
CHROME_BINARY = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CHROMEDRIVER_PATH = r"C:\chromedriver\chromedriver.exe"
# MySQL 配置
DB_CONFIG = {
    'host': '127.0.0.1',
    'user': 'google_maps',
    'password': 'yun@google_maps',
    'database': 'google_maps',
    'raise_on_warnings': True,
    'port': 3306  # 添加端口号
}
# 创建输出目录
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

EMAIL_SERVER = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USERNAME = 'your_email@gmail.com'
EMAIL_PASSWORD = 'new_app_password'
SECRET_KEY = 'your_secret_key'  # 示例，替换为实际值