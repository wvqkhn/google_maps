import sys
import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def wait_for_element(driver, selector, timeout=5):
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
        return element
    except Exception as e:
        print(f"未找到元素 {selector}: {e}", file=sys.stderr)
        return None

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
            time.sleep(3)  # 等待页面加载

            progress = int((i + 1) / len(business_data_list) * 100)
            yield progress, name, None, f"正在访问 {name} 的网站: {website}"

            # 获取页面全部文本
            page_text = driver.find_element(By.TAG_NAME, "body").text

            # 提取 Email
            email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
            emails = re.findall(email_pattern, page_text)
            business['email'] = emails[0] if emails else None
            if business['email']:
                print(f"提取到 {name} 的邮箱: {business['email']}")

            # 提取 Phone
            phone_pattern = r"(\+\d{1,3}\s?)?(\(?\d{2,3}\)?[\s.-]?)?\d{3,4}[\s.-]?\d{4}"
            phones = re.findall(phone_pattern, page_text)
            business['phone'] = phones[0][0] + phones[0][1] if phones else None
            if business['phone']:
                print(f"提取到 {name} 的电话: {business['phone']}")

            # 提取 Facebook
            facebook_elem = wait_for_element(driver, 'a[href*="facebook.com"]', timeout=3)
            business['facebook'] = facebook_elem.get_attribute('href') if facebook_elem else None
            if business['facebook']:
                print(f"提取到 {name} 的 Facebook: {business['facebook']}")
            else:
                facebook_pattern = r"(https?://(?:www\.)?facebook\.com/[^\s]+)"
                facebook_urls = re.findall(facebook_pattern, page_text)
                business['facebook'] = facebook_urls[0] if facebook_urls else None
                if business['facebook']:
                    print(f"通过正则提取到 {name} 的 Facebook: {business['facebook']}")

            print(f"成功提取 {name} 的联系方式: {business}")
            yield progress, name, business, f"成功提取 {name} 的联系方式"

        except Exception as e:
            print(f"提取 {name} 的联系方式时出错: {e}", file=sys.stderr)
            yield progress, name, business, f"提取 {name} 的联系方式失败: {e}"