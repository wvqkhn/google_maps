import sys
import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

def wait_for_element(driver, selector, timeout=5):
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
        return element
    except Exception as e:
        print(f"未找到元素 {selector}: {e}", file=sys.stderr)
        return None

def scroll_page(driver, scroll_times=3, scroll_delay=1):
    """滚动页面以加载动态内容"""
    for i in range(scroll_times):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_delay)

def is_valid_email(email):
    """验证是否为有效邮箱，排除图片文件名等无效项"""
    invalid_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg')
    invalid_patterns = [r'\d+x\d*', r'logo', r'image', r'img']  # 排除常见图片模式，如 180x, logo
    email_lower = email.lower()
    # 检查是否包含图片扩展名或模式
    if any(email_lower.endswith(ext) for ext in invalid_extensions) or \
       any(re.search(pattern, email_lower) for pattern in invalid_patterns):
        return False
    # 检查长度和基本格式
    return len(email) <= 254 and re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email) is not None

def extract_contact_info(driver, business_data_list):
    """访问每个商家的网站并提取联系方式"""
    for i, business in enumerate(business_data_list):
        name = business['name']
        website = business.get('website')
        if not website:
            print(f"{name} 无网站，跳过联系方式提取")
            yield i, name, business, f"{name} 无网站，跳过"
            continue

        try:
            print(f"访问网站: {website} 以提取联系方式")
            driver.get(website)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            scroll_page(driver, scroll_times=3, scroll_delay=1)

            progress = int((i + 1) / len(business_data_list) * 100)
            yield progress, name, None, f"正在访问 {name} 的网站: {website}"

            # 获取主页面内容
            page_text = driver.find_element(By.TAG_NAME, "body").text
            page_source = driver.page_source

            # 初始化联系方式
            emails = set()
            phones = set()

            # 提取 Emails 和 Phones（主页面）
            email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
            phone_pattern = r"(\+?\d{1,4}[\s.-]?)?(\(?\d{2,4}\)?[\s.-]?)?\d{3,4}[\s.-]?\d{4,6}|\d{8,14}"

            # 从文本和源代码提取邮箱
            raw_emails = re.findall(email_pattern, page_text) + re.findall(email_pattern, page_source)
            print(f"{name} 原始邮箱匹配: {raw_emails}")
            for email in raw_emails:
                if is_valid_email(email):
                    emails.add(email)

            # 从 mailto 链接提取邮箱
            mailto_links = driver.find_elements(By.CSS_SELECTOR, 'a[href^="mailto:"]')
            for link in mailto_links:
                href = link.get_attribute('href')
                mailto_match = re.search(r"mailto:([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", href)
                if mailto_match and is_valid_email(mailto_match.group(1)):
                    emails.add(mailto_match.group(1))

            # 提取电话
            phone_matches = re.findall(phone_pattern, page_text)
            for phone_tuple in phone_matches:
                phone = ''.join(filter(None, phone_tuple)).replace(' ', '').replace('-', '').replace('.', '').replace('(', '').replace(')', '')
                if len(phone) >= 8:
                    phones.add(phone)

            # 尝试点击“联系我们”或类似链接
            contact_keywords = [
                'contact', '联系', 'about', '关于', 'get in touch', '联系我们',
                'support', '帮助', 'customer service', '客户服务'
            ]
            contact_link = None
            for keyword in contact_keywords:
                contact_link = wait_for_element(driver, f'a[href*="{keyword}"], a:contains("{keyword}")', timeout=2)
                if contact_link:
                    break
            if contact_link:
                try:
                    print(f"找到 {name} 的联系链接: {contact_link.get_attribute('href')}")
                    ActionChains(driver).move_to_element(contact_link).click().perform()
                    WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    scroll_page(driver, scroll_times=2, scroll_delay=1)
                    contact_page_text = driver.find_element(By.TAG_NAME, "body").text
                    contact_page_source = driver.page_source
                    raw_emails = re.findall(email_pattern, contact_page_text) + re.findall(email_pattern, contact_page_source)
                    print(f"{name} 联系页面原始邮箱匹配: {raw_emails}")
                    for email in raw_emails:
                        if is_valid_email(email):
                            emails.add(email)
                    mailto_links = driver.find_elements(By.CSS_SELECTOR, 'a[href^="mailto:"]')
                    for link in mailto_links:
                        href = link.get_attribute('href')
                        mailto_match = re.search(r"mailto:([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", href)
                        if mailto_match and is_valid_email(mailto_match.group(1)):
                            emails.add(mailto_match.group(1))
                    phone_matches = re.findall(phone_pattern, contact_page_text)
                    for phone_tuple in phone_matches:
                        phone = ''.join(filter(None, phone_tuple)).replace(' ', '').replace('-', '').replace('.', '').replace('(', '').replace(')', '')
                        if len(phone) >= 8:
                            phones.add(phone)
                    print(f"从 {name} 的联系页面提取到额外信息")
                except Exception as e:
                    print(f"点击 {name} 的联系页面失败: {e}")

            # 保存提取结果
            business['emails'] = list(emails) if emails else []
            business['phones'] = list(phones) if phones else []
            if business['emails']:
                print(f"提取到 {name} 的邮箱: {business['emails']}")
            else:
                print(f"未在 {name} 的网站找到邮箱")
            if business['phones']:
                print(f"提取到 {name} 的电话: {business['phones']}")
            else:
                print(f"未在 {name} 的网站找到电话")

            # 提取社交媒体和其他联系方式
            social_platforms = {
                'facebook': ('facebook.com', 'Facebook'),
                'twitter': ('twitter.com', 'Twitter'),
                'instagram': ('instagram.com', 'Instagram'),
                'linkedin': ('linkedin.com', 'LinkedIn'),
                'whatsapp': ('wa.me', 'WhatsApp'),
                'youtube': ('youtube.com', 'YouTube')
            }
            for key, (domain, label) in social_platforms.items():
                elem = wait_for_element(driver, f'a[href*="{domain}"]', timeout=2)
                business[key] = elem.get_attribute('href') if elem else None
                if not business[key]:
                    pattern = rf"(https?://(?:www\.)?{domain}/[^\s]+)"
                    urls = re.findall(pattern, page_text)
                    business[key] = urls[0] if urls else None
                if business[key]:
                    print(f"提取到 {name} 的 {label}: {business[key]}")

            print(f"成功提取 {name} 的联系方式: {business}")
            yield progress, name, business, f"成功提取 {name} 的联系方式"

        except Exception as e:
            print(f"提取 {name} 的联系方式时出错: {e}", file=sys.stderr)
            yield progress, name, business, f"提取 {name} 的联系方式失败: {e}"