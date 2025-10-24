from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import json
import os
import re
import tempfile

BASE_URL = "https://www.jdsports.de/frauen/frauenkleidung/"
JSON_FILE = "jdsports_products.json"
BATCH_SIZE = 100  # сохранять каждые 10 товаров
MAX_PRODUCTS_PER_CATEGORY = 100  # максимум товаров с категории

# Настройки Selenium
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
# Add argument to use a temporary user data directory
options.add_argument(f"--user-data-dir={tempfile.mkdtemp()}")
driver = webdriver.Chrome(options=options)

def get_categories():
    driver.get(BASE_URL)
    time.sleep(2)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    categories = []
    filter_blocks = soup.select('div[data-e2e="product-listing-filter-wrap"]')
    for block in filter_blocks:
        title_tag = block.find("h4")
        if title_tag and "Kategorien" in title_tag.text:
            cat_ul = block.select_one("ul.list-filters")
            for a in cat_ul.select("li a.filterLink"):
                name = a.select_one("span").text.strip()
                href = "https://www.jdsports.de" + a['href']
                categories.append((name, href))
            break
    return categories

def load_full_page():
    while True:
        try:
            mehr_btn = driver.find_element(By.CSS_SELECTOR, "span.btn.rppLnk.showMore")
            if mehr_btn.is_displayed():
                driver.execute_script("arguments[0].click();", mehr_btn)
                time.sleep(1.5)
            else:
                break
        except:
            break

def extract_color_from_url(url: str) -> str:
    match = re.search(r"/product/([a-zA-Zäöüß-]+)-", url)
    if match:
        color_raw = match.group(1)
        color_word = color_raw.split("-")[0]  # берём только первое слово
        return color_word.replace("-", " ").capitalize()
    return ""

def get_products_from_page(category_name):
    soup = BeautifulSoup(driver.page_source, "html.parser")
    items = soup.select("li.productListItem")
    products = []
    for item in items:
        title_tag = item.select_one("span.itemTitle a")
        price_tag = item.select_one("span.pri")
        img_tag = item.select_one("img.thumbnail")
        if not title_tag:
            continue
        href = title_tag.get("href", "")
        full_url = "https://www.jdsports.de" + href
        products.append({
            "title": title_tag.text.strip(),
            "price": price_tag.text.strip() if price_tag else "",
            "img_url": img_tag['src'] if img_tag else "",
            "ref_item": full_url,
            "category": category_name,
            "sex": 1,
            "shop_id": 10,
            "color": extract_color_from_url(href)  # Цвет сразу из ссылки
        })
    return products

def get_product_sizes(product, retries=3):
    url = product['ref_item']
    for attempt in range(retries):
        try:
            driver.set_page_load_timeout(40)
            driver.get(url)
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div#productSizeStock button[data-e2e='pdp-productDetails-size']"))
            )
            time.sleep(1)
            soup = BeautifulSoup(driver.page_source, "html.parser")
            sizes = [btn['data-size'] for btn in soup.select("div#productSizeStock button[data-e2e='pdp-productDetails-size']")]
            product['size'] = sizes
            return product
        except TimeoutException:
            driver.execute_script("window.stop();")
            time.sleep(1)
        except Exception as e:
            print(f"Ошибка при получении размеров {url}: {e}")
            time.sleep(1)
    product['size'] = []
    return product

def save_products_batch(products, filename=JSON_FILE):
    if not products:
        return
    if not os.path.exists(filename):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
    else:
        with open(filename, "r+", encoding="utf-8") as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                existing_data = []
            existing_data.extend(products)
            f.seek(0)
            json.dump(existing_data, f, ensure_ascii=False, indent=2)

# Основной цикл
categories = get_categories()

for cat_name, cat_url in categories:
    print(f"Парсим категорию: {cat_name}")
    driver.get(cat_url)
    time.sleep(2)

    batch = []
    products_count = 0  # счётчик товаров по категории

    while products_count < MAX_PRODUCTS_PER_CATEGORY:
        load_full_page()
        products = get_products_from_page(cat_name)

        for prod in products:
            if products_count >= MAX_PRODUCTS_PER_CATEGORY:
                break
            prod = get_product_sizes(prod)
            batch.append(prod)
            products_count += 1

            if len(batch) >= BATCH_SIZE:
                save_products_batch(batch)
                print(f"Сохранено {len(batch)} товаров...")
                batch = []

        # Переходим на следующую страницу
        try:
            next_page = driver.find_element(By.CSS_SELECTOR, "a.btn.pageNav[rel='next']")
            if next_page.is_displayed():
                driver.execute_script("arguments[0].click();", next_page)
                time.sleep(2)
            else:
                break
        except:
            break

    if batch:
        save_products_batch(batch)
        print(f"Сохранено оставшихся {len(batch)} товаров.")

driver.quit()
print("Парсинг завершен.")