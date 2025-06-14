import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
from db import update_send_count  # 导入数据库更新函数

try:
    from config import EMAIL_SERVER, EMAIL_PORT, EMAIL_USERNAME, EMAIL_PASSWORD
except ImportError:
    # 如果 config.py 缺失，从环境变量加载
    EMAIL_SERVER = os.getenv("EMAIL_SERVER", "smtp.gmail.com")
    EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
    EMAIL_USERNAME = os.getenv("EMAIL_USERNAME")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
class EmailSender:
    def __init__(self):
        """
        Initializes the EmailSender class with Gmail server details.
        Replace with your actual Gmail username and password/app password.
        """
        self.mail_server = EMAIL_SERVER
        self.mail_port = EMAIL_PORT
        self.mail_username = EMAIL_USERNAME
        self.mail_password = EMAIL_PASSWORD

        # 验证必需配置
        if not self.mail_username or not self.mail_password:
            raise ValueError("必须在 config.py 或环境变量中设置 EMAIL_USERNAME 和 EMAIL_PASSWORD。")

    def send_email(self, recipient, subject, body, attachment_path=None):
        """
        Sends an email using Gmail.
        """
        try:
            msg = MIMEMultipart()
            msg['From'] = self.mail_username
            msg['To'] = recipient
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'html')) # Assuming body is HTML

            # if attachment_path:
            #     try:
            #         with open(attachment_path, "rb") as attachment:
            #             part = MIMEBase("application", "octet-stream")
            #             part.set_payload(attachment.read())
            #         encoders.encode_base64(part)
            #         part.add_header('Content-Disposition', f"attachment; filename= {os.path.basename(attachment_path)}")
            #         msg.attach(part)
            #     except FileNotFoundError:
            #         return False, "Attachment file not found."

            with smtplib.SMTP(self.mail_server, self.mail_port) as server:
                server.starttls()
                server.login(self.mail_username, self.mail_password)
                server.sendmail(self.mail_username, recipient, msg.as_string())
                update_send_count([recipient])
                # 邮件发送成功后，更新数据库中的 send_count


            return True, "Email sent successfully"
        except Exception as e:
            return False, str(e)