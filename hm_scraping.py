from bs4 import BeautifulSoup
import time
import json
import random
import undetected_chromedriver as uc
from fake_useragent import UserAgent
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re

BASE_URL = "https://www2.hm.com/de_de/damen/neuheiten/kleidung.html?page=3"


def create_driver(use_proxy=False, proxy=None):
    ua = UserAgent()
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.headless = False  # Отключаем headless для отладки
    options.add_argument("--window-size=1920,1080")
    options.add_argument(f"user-agent={ua.random}")
    options.add_argument("--accept-language=en-US,en;q=0.9")
    options.add_argument("--accept=text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8")
    options.binary_location = "/usr/bin/chromium"  # Замени на "/usr/bin/google-chrome", если нужно

    if use_proxy and proxy:
        options.add_argument(f"--proxy-server={proxy}")

    driver = uc.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver


def get_soup(driver):
    return BeautifulSoup(driver.page_source, "lxml")


def get_product_links():
    driver = create_driver()
    driver.get(BASE_URL)

    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/de_de/productpage.']"))
        )
    except:
        print("⚠️ Не дождались загрузки ссылок")

    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(3, 5))
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    # Отладочный вывод HTML
    with open("debug_page.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    print("📝 Сохранён HTML страницы в debug_page.html для отладки")

    soup = get_soup(driver)
    driver.quit()

    links = []
    for a in soup.select("a[href^='/de_de/productpage.']"):
        href = a.get("href")
        if href:
            full_link = "https://www2.hm.com" + href.split("?")[0]
            if full_link not in links:
                links.append(full_link)

    print(f"✅ Найдено ссылок: {len(links)}")
    return links


def parse_product_page(url):
    driver = create_driver()
    driver.get(url)

    # Имитация человеческого поведения
    driver.execute_script("window.scrollBy(0, 500);")
    time.sleep(random.uniform(1, 2))

    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1, span[class*='price']"))
        )
    except:
        print(f"⚠️ Не дождался данных на {url}")

    soup = get_soup(driver)
    driver.quit()

    data = {
        "title": None,
        "category": None,
        "size": [],
        "color": [],
        "price": None,
        "img_url": None,
        "ref_item": url,
        "shop_id": 1,
        "sex": 0
    }

    # Извлекаем JSON из __NEXT_DATA__
    next_data_script = soup.find("script", id="__NEXT_DATA__")
    if next_data_script:
        try:
            json_data = json.loads(next_data_script.string)
            product = json_data['props']['pageProps']['product']

            data["title"] = product.get('name')
            data["img_url"] = product.get('whitePrice', {}).get('image', {}).get(
                'url')  # Или из галереи: product['galleryImages'][0]['baseUrl']
            data["price"] = product.get('whitePrice', {}).get('formattedValue') or product.get('redPrice', {}).get(
                'formattedValue')
            data["category"] = product.get('categoryName') or product.get('mainCategoryCode')

            # Цвета: из variantsList
            colors = set()
            for variant in product.get('variantsList', []):
                color_hex = variant.get('rgbColors', [{}])[0].get('hex')
                if color_hex:
                    colors.add(color_hex)
            data["color"] = list(colors)

            # Размеры: из sizes
            sizes = [size.get('name') for size in product.get('sizes', []) if size.get('name')]
            data["size"] = sizes[:5]  # Ограничим до 5

        except (json.JSONDecodeError, KeyError) as e:
            print(f"Ошибка парсинга JSON на {url}: {e}")

    # Фоллбек на старые селекторы, если JSON не сработал
    if not data["title"]:
        title_tag = soup.select_one("h1")
        if title_tag:
            data["title"] = title_tag.get_text(strip=True)
        else:
            meta_title = soup.select_one("meta[property='og:title']")
            data["title"] = meta_title["content"] if meta_title else None

    if not data["price"]:
        price_tag = soup.find("span", string=lambda s: s and "€" in s)
        if price_tag:
            data["price"] = price_tag.get_text(strip=True)

    if not data["color"]:
        colors = []

        color_elements = soup.select(
            "section[data-testid='color-selector'] a[title], section[data-testid='color-selector'] img[alt]")

        for el in color_elements:
            color = el.get("title") or el.get("alt")
            if color:
                colors.append(color.strip())

        data["color"] = list(dict.fromkeys(colors))

    if not data["size"]:
        size_divs = soup.find_all("div", attrs={"aria-label": lambda v: v and "Größe" in v})
        sizes = [div.get_text(strip=True) for div in size_divs if div.get_text(strip=True)]

        data["size"] = sizes[1:]

    if not data["img_url"]:
        img_tag = soup.select_one("meta[property='og:image']")
        if img_tag:
            data["img_url"] = img_tag["content"]

    if not data["category"]:
        cat_tag = soup.find("article", attrs={"data-category": True})
        if cat_tag:
            data["category"] = cat_tag["data-category"]

    print(data)
    return data


def main():
    all_products = []
    links = get_product_links()

    for i, link in enumerate(links, 1):
        print(f"[{i}/{len(links)}] {link}")
        try:
            product_data = parse_product_page(link)
            all_products.append(product_data)
        except Exception as e:
            print(f"Ошибка при парсинге {link}: {e}")
        time.sleep(random.uniform(3, 5))

    with open("hm_data_2.json", "w", encoding="utf-8") as f:
        json.dump(all_products, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Сохранено {len(all_products)} товаров в hm_data.json")


if __name__ == "__main__":
    main()