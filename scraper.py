import time
import re
import sys
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

def wait_for_element(driver, selector, timeout=10):
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
        return element
    except Exception as e:
        print(f"未找到元素 {selector}: {e}", file=sys.stderr)
        return None

def scroll_and_load_more(driver, max_scrolls=5, scroll_delay=3, target_count=10):
    previous_link_count = 0
    business_links = []
    for i in range(max_scrolls):
        business_links = driver.find_elements(By.CSS_SELECTOR,
                                              'a[role="link"][aria-label], a.hfpxzc, a[href*="/maps/place/"]')
        current_link_count = len(business_links)
        print(f"滚动 {i + 1}/{max_scrolls} - 当前商家链接数量: {current_link_count}")

        if current_link_count >= target_count:
            print(f"已达到目标条数 {target_count}，停止滚动")
            business_links = business_links[:target_count]
            break

        if i > 0 and current_link_count == previous_link_count:
            print("链接数量不再增加，停止滚动")
            break

        previous_link_count = current_link_count
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_delay)

    print(f"滚动完成，最终找到 {len(business_links)} 个商家链接")
    return business_links

def extract_single_business_info(driver):
    results = []
    try:
        time.sleep(5)
        name_elem = wait_for_element(driver, 'h1.DUwDvf')
        name = name_elem.text.strip() if name_elem else "Unknown"

        business_data = {'name': name}

        address_elem = wait_for_element(driver, 'button[aria-label*="Address:"], div[data-item-id="address"]')
        if address_elem:
            business_data['address'] = (address_elem.get_attribute('aria-label') or address_elem.text).replace('Address: ', '').strip()

        hours_elem = wait_for_element(driver, 'span.ZDu9vd, div[data-item-id="oh"]')
        if hours_elem:
            business_data['hours'] = hours_elem.text.strip()

        website_elem = wait_for_element(driver, 'a[aria-label*="Website:"], a[data-item-id="authority"]')
        if website_elem:
            business_data['website'] = website_elem.get_attribute('href')

        phone_elem = wait_for_element(driver, 'button[aria-label*="Phone:"], div[data-item-id="phone"]')
        if phone_elem:
            business_data['phone'] = (phone_elem.get_attribute('aria-label') or phone_elem.text).replace('Phone: ', '').strip()

        plus_code_elem = wait_for_element(driver, 'button[aria-label*="Plus code:"], div[data-item-id="oloc"]')
        if plus_code_elem:
            business_data['plusCode'] = (plus_code_elem.get_attribute('aria-label') or plus_code_elem.text).replace('Plus code: ', '').strip()

        results.append(business_data)
        print(f"成功提取 {name} 的信息: {business_data}")
        return results, f"完成单个商家数据提取: {name}"
    except Exception as e:
        print(f"提取单个商家信息时出错: {e}", file=sys.stderr)
        return results, f"提取单个商家信息时出错: {e}"

def extract_business_info(driver, search_url, limit=10):
    print(f"正在访问 URL: {search_url}")
    try:
        driver.get(search_url)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'body'))
        )
    except Exception as e:
        print(f"访问 URL 失败: {e}", file=sys.stderr)
        return [], f"访问 URL 失败: {e}"

    if "/place/" in search_url:
        print("检测到单个商家页面，直接提取信息...")
        return extract_single_business_info(driver)

    print("开始滚动页面以加载更多商家...")
    business_links = scroll_and_load_more(driver, max_scrolls=10, scroll_delay=2, target_count=limit)

    if not business_links:
        print("未找到任何商家链接")
        return [], "未找到任何商家链接"

    results = []
    total = len(business_links)
    for i, link in enumerate(business_links):
        if len(results) >= limit:
            print(f"已提取 {limit} 条数据，停止提取")
            break

        try:
            name = link.get_attribute('aria-label') or link.text
            if not name:
                continue
            name = name.replace('Visited link', '').strip()

            print(f"点击商家: {name}")
            ActionChains(driver).move_to_element(link).click().perform()
            time.sleep(3)

            current_url = driver.current_url
            if "/maps/place/" not in current_url:
                print(f"未跳转到商家详情页，当前 URL: {current_url}")
                continue

            info_panel_selectors = [
                'div[role="region"][aria-label*="Information for"]',
                'div[role="region"][aria-label*="商家信息"]',
                'div[role="main"]',
                'div.m6QErb',
                'div.W4Efsd',
                'div.fontBodyMedium',
                'div[aria-label*="Business information"]'
            ]
            info_panel = None
            for selector in info_panel_selectors:
                info_panel = wait_for_element(driver, selector, timeout=15)
                if info_panel:
                    print(f"使用选择器 {selector} 找到信息面板")
                    break

            if not info_panel:
                print(f"未找到 {name} 的信息面板，跳过")
                continue

            business_data = {'name': name}
            all_elements = info_panel.find_elements(By.CSS_SELECTOR,
                                                    'button[aria-label], div[data-item-id], div.Io6YTe, div.W4Efsd, span.ZDu9vd, a[href], div.fontBodyMedium, div[role="main"] div')

            business_data['address'] = None
            business_data['hours'] = None
            business_data['website'] = None
            business_data['phone'] = None
            business_data['plusCode'] = None

            for elem in all_elements:
                text = (elem.get_attribute('aria-label') or elem.text).strip()
                if not text:
                    continue

                if ('Address:' in text or '地址' in text) and not business_data['address']:
                    address_text = text.replace('Address: ', '').replace('地址：', '').strip()
                    if not re.match(r'^\d+\.\d+\(\d+\)', address_text):
                        business_data['address'] = address_text

                if ('hours' in text.lower() or '营业时间' in text or 'Open' in text or 'Closed' in text) and not business_data['hours']:
                    hours_text = text.strip()
                    if not re.match(r'^\d+\.\d+\(\d+\)', hours_text) and any(day in hours_text.lower() for day in ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun', 'open', 'closed']):
                        business_data['hours'] = hours_text

                if ('Phone:' in text or '电话' in text or re.match(r'\+?\d[\d\s-]+', text)) and not business_data['phone']:
                    phone_text = text.replace('Phone: ', '').replace('电话：', '').strip()
                    if re.match(r'\+?\d[\d\s-]+', phone_text):
                        business_data['phone'] = phone_text

                if ('Website:' in text or '网站' in text or elem.get_attribute('href')) and not business_data['website']:
                    href = elem.get_attribute('href')
                    if href and ('http' in href or 'www' in href) and 'google.com/maps' not in href:
                        business_data['website'] = href

                if ('Plus code:' in text or 'Plus Code' in text or re.match(r'[A-Z0-9]+\+[A-Z0-9]+', text)) and not business_data['plusCode']:
                    plus_code_text = text.replace('Plus code: ', '').strip()
                    if re.match(r'[A-Z0-9]+\+[A-Z0-9]+', plus_code_text):
                        business_data['plusCode'] = plus_code_text

            results.append(business_data)
            print(f"成功提取 {name} 的信息: {business_data}")
            progress = int((i + 1) / total * 100)
            yield progress, name, business_data, None  # 使用生成器返回进度和数据

        except Exception as e:
            print(f"提取 {name} 时出错: {e}", file=sys.stderr)
            continue

    yield 100, None, None, "数据提取完成"  # 任务完成
