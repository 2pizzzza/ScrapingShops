from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import json
import time
import random


URLS = [
    "https://www.adidas.de/manner-kleidung",  # all
    "https://www.adidas.de/manner-kleidung-t_shirts",  # T-shirts
    "https://www.adidas.de/manner-kleidung-trainingsanzuge",  # Trainingsanzüge
    "https://www.adidas.de/manner-kleidung-hosen",  # Hosen
    "https://www.adidas.de/manner-kleidung-shorts",  # Shorts
    "https://www.adidas.de/manner-kleidung-jacken",  # Jacken
    "https://www.adidas.de/manner-kleidung-trainingsjacken",  # Trainingsjacken
    "https://www.adidas.de/manner-kleidung-hoodies",  # Hoodies
    "https://www.adidas.de/manner-kleidung-poloshirts",  # Poloshirts
]


# 🎨 цвета
COLORS = [
    "Schwarz", "Weiß", "Blau", "Grün", "Grau", "Rot", "Lila", "Rosa", "Braun",
    "Beige", "Weinrot", "Orange", "Türkis", "Mehrfarbig", "Gelb", "Silber", "Gold"
]

# 📏 размеры
SIZES = [
    "3XS", "2XS", "XS", "S", "M", "L", "XL", "2XL", "3XL", "4XL", "5XL", "1X", "2X", "3X", "4X",
    "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30",
    "31", "32", "33", "34", "35", "36", "37", "38", "39", "40", "41", "42", "43", "44", "45",
    "46", "47", "48", "49", "50", "51", "52", "53", "54", "55", "56", "62", "68", "74", "80",
    "86", "92", "98", "104", "110", "116", "122", "128", "134", "140", "146", "152", "158",
    "164", "170", "176", "27-30", "31-34", "35-38", "39-42", "40-42", "43-46", "43-47", "48-51",
    "Erwachsene (S/M)", "Erwachsene (M/L)", "Erwachsene (L/XL)", "Kinder", "Teens", "1 Größe",
    "Kleinkinder", "OSFM", "OSFW", "6XL", "16-18", "19-21", "22-24", "25-27", "28-30", "31-33",
    '33"', "34-36", '35"', "37-39", '42"', "43-45", '44"', "46-48", "49-51", "52-54", '36.5"'
]


def get_driver():
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=options)
    return driver


def get_page_source(url):
    driver = get_driver()
    driver.get(url)

    # ждём подгрузку JS
    time.sleep(7)

    # прокручиваем вниз, чтобы загрузились все товары
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    html = driver.page_source
    driver.quit()
    return html


def parse_adidas_products(html, category_label):
    soup = BeautifulSoup(html, "html.parser")
    product_cards = soup.select("main[data-testid='product-grid'] article[data-testid='plp-product-card']")
    products = []

    for card in product_cards:
        try:
            title_tag = card.select_one("p[data-testid='product-card-title']")
            title = title_tag.get_text(strip=True) if title_tag else None

            price_tag = card.select_one("div[data-testid='main-price'] span:last-child")
            price = price_tag.get_text(strip=True) if price_tag else None

            link_tag = card.select_one("a[data-testid='product-card-description-link']")
            ref_item = link_tag["href"] if link_tag else None
            if ref_item and not ref_item.startswith("http"):
                ref_item = "https://www.adidas.de" + ref_item

            img_tag = card.select_one("img[data-testid='product-card-primary-image']")
            img_url = img_tag["src"] if img_tag else None

            # 🎲 случайные цвета и размеры
            random_colors = random.sample(COLORS, k=random.randint(1, 3))
            random_sizes = random.sample(SIZES, k=random.randint(3, 7))

            product = {
                "title": title,
                "category": category_label,
                "size": random_sizes,
                "color": random_colors,
                "price": price,
                "img_url": img_url,
                "ref_item": ref_item,
                "shop_id": 2,
                "sex": 1
            }

            products.append(product)

        except Exception as e:
            print(f"Ошибка при парсинге товара: {e}")

    return products


def main():
    all_products = []

    for url in URLS:
        print(f"\n🔍 Парсим: {url}")
        html = get_page_source(url)
        # достаём категорию из комментария к ссылке
        category_label = url.split("manner-kleidung-")[-1] if "-" in url else "all"
        products = parse_adidas_products(html, category_label)
        print(f"✅ Найдено {len(products)} товаров в категории {category_label}")
        all_products.extend(products)

    with open("jsons/adidas_products.json", "w", encoding="utf-8") as f:
        json.dump(all_products, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Сохранено всего {len(all_products)} товаров в adidas_products.json")


if __name__ == "__main__":
    main()
