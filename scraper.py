import sys
import time
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

def scroll_and_load_more(driver, max_scrolls=50, scroll_delay=3, target_count=500):
    business_links = set()  # 使用 set 避免重复链接
    min_scrolls = 5  # 至少滚动 5 次

    # 定位左侧商家列表的滚动区域
    scrollable_area = wait_for_element(driver, 'div[role="feed"], div[aria-label*="results"], div.m6QErb[style*="overflow: auto"], div[style*="overflow-y: scroll"]')
    if not scrollable_area:
        print("未找到左侧滚动区域，尝试整个页面滚动")
        scrollable_area = driver.find_element(By.TAG_NAME, "body")

    for i in range(max_scrolls):
        # 获取当前所有可见链接
        new_links = driver.find_elements(By.CSS_SELECTOR,
                                         'a[role="link"][aria-label], a.hfpxzc, a[href*="/maps/place/"]')
        for link in new_links:
            href = link.get_attribute('href') or link.text
            if href:
                business_links.add(href)
        current_link_count = len(business_links)
        print(f"滚动 {i + 1}/{max_scrolls} - 当前唯一商家链接数量: {current_link_count}")

        if current_link_count >= target_count:
            print(f"已达到或超过目标条数 {target_count}，停止滚动")
            break

        # 模拟滚轮向下滚动
        ActionChains(driver).move_to_element(scrollable_area).click().send_keys(Keys.PAGE_DOWN).perform()
        time.sleep(scroll_delay)  # 等待加载新数据

        # 检查是否还有新链接加载
        new_links_after_scroll = driver.find_elements(By.CSS_SELECTOR,
                                                      'a[role="link"][aria-label], a.hfpxzc, a[href*="/maps/place/"]')
        for link in new_links_after_scroll:
            href = link.get_attribute('href') or link.text
            if href:
                business_links.add(href)
        if i >= min_scrolls and len(business_links) == current_link_count:
            print("链接数量不再增加，停止滚动")
            break

    # 转换为列表并截取目标数量
    business_links = list(business_links)[:target_count]
    print(f"滚动完成，最终找到 {len(business_links)} 个唯一商家链接")
    return business_links

def extract_single_business_info(driver):
    results = []
    try:
        time.sleep(3)  # 确保页面加载
        name_elem = wait_for_element(driver, 'h1.DUwDvf')
        name = name_elem.text.strip() if name_elem else "Unknown"

        business_data = {'name': name, 'website': None}

        # 提取网站
        website_elem = wait_for_element(driver, 'a[aria-label*="Website:"], a[data-item-id="authority"]')
        if website_elem:
            href = website_elem.get_attribute('href')
            business_data['website'] = href
            print(f"提取到网站: {href}")
        else:
            print(f"未找到 {name} 的网站元素，使用备用选择器")
            website_elem = wait_for_element(driver, 'a[href^="http"]:not([href*="google.com"])')
            if website_elem:
                href = website_elem.get_attribute('href')
                business_data['website'] = href
                print(f"备用选择器提取到网站: {href}")

        results.append(business_data)
        print(f"成功提取 {name} 的信息: {business_data}")
        return results, f"完成单个商家数据提取: {name}"
    except Exception as e:
        print(f"提取单个商家信息时出错: {e}", file=sys.stderr)
        return results, f"提取单个商家信息时出错: {e}"

def extract_business_info(driver, search_url, limit=500):
    print(f"正在访问 URL: {search_url}，目标提取数量: {limit}")
    try:
        driver.get(search_url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'body'))
        )
    except Exception as e:
        print(f"访问 URL 失败: {e}", file=sys.stderr)
        return [], f"访问 URL 失败: {e}"

    if "/place/" in search_url:
        print("检测到单个商家页面，直接提取信息...")
        return extract_single_business_info(driver)

    print("开始滚动页面以加载更多商家...")
    business_links = scroll_and_load_more(driver, max_scrolls=50, scroll_delay=3, target_count=limit)

    if not business_links:
        print("未找到任何商家链接")
        return [], "未找到任何商家链接"

    results = []
    total = len(business_links)
    print(f"共有 {total} 个商家链接可供提取")
    for i, link_href in enumerate(business_links):
        if len(results) >= limit:
            print(f"已提取 {limit} 条数据，停止提取")
            break

        try:
            # 根据 href 重新定位元素
            link = driver.find_element(By.XPATH, f"//a[@href='{link_href}' or text()='{link_href}']")
            name = link.get_attribute('aria-label') or link.text
            if not name:
                continue
            name = name.replace('Visited link', '').strip()

            print(f"点击商家: {name}")
            ActionChains(driver).move_to_element(link).click().perform()
            time.sleep(3)  # 确保页面加载

            current_url = driver.current_url
            if "/maps/place/" not in current_url:
                print(f"未跳转到商家详情页，当前 URL: {current_url}")
                continue

            info_panel = wait_for_element(driver, 'div[role="region"][aria-label*="Information for"], div.m6QErb')
            if not info_panel:
                print(f"未找到 {name} 的信息面板，跳过")
                continue
            print(f"找到 {name} 的信息面板")

            business_data = {'name': name, 'website': None}

            # 精准提取网站
            website_elem = wait_for_element(driver, 'a[aria-label*="Website:"], a[data-item-id="authority"]', timeout=3)
            if website_elem:
                href = website_elem.get_attribute('href')
                business_data['website'] = href
                print(f"提取到网站: {href}")
            else:
                print(f"未找到 {name} 的网站元素，使用备用选择器")
                website_elem = wait_for_element(driver, 'a[href^="http"]:not([href*="google.com"])', timeout=3)
                if website_elem:
                    href = website_elem.get_attribute('href')
                    business_data['website'] = href
                    print(f"备用选择器提取到网站: {href}")

            results.append(business_data)
            print(f"成功提取 {name} 的信息: {business_data}")
            progress = int((i + 1) / total * 100) if total > 0 else 100
            yield progress, name, business_data, None

        except Exception as e:
            print(f"提取 {link_href} 时出错: {e}", file=sys.stderr)
            continue

    yield 100, None, None, "数据提取完成"