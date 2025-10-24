from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

MEN_URL = "https://en.zalando.de/mens-clothing/"


def create_driver():
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--headless")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    return driver


def get_soup(url, delay=1):
    driver = create_driver()
    driver.get(url)
    time.sleep(delay)
    soup = BeautifulSoup(driver.page_source, "lxml")
    driver.quit()
    return soup


def get_categories(soup):
    categories = []
    ul = soup.select_one('ul._3ObVF2.m3OCL3._4oK5GO.-hyY7t ')
    if ul:
        for a in ul.select("a[href]"):
            href = a["href"]
            name = a.get_text(strip=True)
            if href.startswith("http"):
                categories.append({"name": name, "url": href})
    else:
        print("❌ Блок категорий не найден")
    return categories


def get_product_info(product_url):
    """Собирает информацию о товаре с его страницы"""
    soup = get_soup(product_url)

    # Title
    title_tag = soup.select_one("h1")
    title = title_tag.get_text(strip=True) if title_tag else ""

    # Description
    desc_tag = soup.select_one("div[itemprop='description'] p")
    description = desc_tag.get_text(strip=True) if desc_tag else ""

    # Category (можно взять из хлебных крошек, если есть)
    cat_tag = soup.select("nav.breadcrumbs a")
    category = " > ".join([c.get_text(strip=True) for c in cat_tag]) if cat_tag else ""

    # Sizes
    size_tags = soup.select("button.size-selector")  # пример, нужно уточнить селектор
    sizes = [s.get_text(strip=True) for s in size_tags] if size_tags else []

    # Color
    color_tag = soup.select_one("div.color-selector img")
    color = color_tag.get("alt") if color_tag else ""

    # Price
    price_tag = soup.select_one("p span.price")  # пример
    price = price_tag.get_text(strip=True) if price_tag else ""

    # Image URL
    img_tag = soup.select_one("img.product-image")
    img_url = img_tag.get("src") if img_tag else ""

    # Ref item / Shop ID / Sex (можно задать статично или вытаскивать с сайта)
    ref_item = product_url.split("/")[-1].replace(".html", "")
    shop_id = "zalando"
    sex = "men"

    return {
        "title": title,
        "description": description,
        "category": category,
        "size": sizes,
        "color": color,
        "price": price,
        "img_url": img_url,
        "ref_item": ref_item,
        "shop_id": shop_id,
        "sex": sex,
        "url": product_url
    }


def get_products(cat_url):
    """Собирает все товары из категории и их детали"""
    soup = get_soup(cat_url)
    products = []

    ul = soup.select_one("ul.AnNemq._0xLoFW._7ckuOK.mROyo1")
    if not ul:
        print("❌ Блок товаров не найден")
        return products

    for li in ul.select("li.QjLAB7._75qWlu.iOzucJ"):
        a_tag = li.select_one("a[href]")
        if a_tag:
            product_url = a_tag["href"]
            if product_url.startswith("http"):
                info = get_product_info(product_url)
                products.append(info)

    return products


def main():
    soup = get_soup(MEN_URL)

    categories = get_categories(soup)
    print(f"🔹 Найдено категорий: {len(categories)}")
    for c in categories:
        print(f"{c['name']} → {c['url']}")

    if categories:
        first_cat = categories[1]  # если хочешь вторую категорию
        print(f"\n🔹 Сбор товаров из категории: {first_cat['name']}")

        # Получаем все товары с полной информацией
        products = get_products(first_cat["url"])
        print(f"🔹 Найдено товаров: {len(products)}\n")

        # Выводим первые 10 товаров
        for p in products[:10]:
            print("------")
            print(f"Title: {p['title']}")
            print(f"Description: {p['description']}")
            print(f"Category: {p['category']}")
            print(f"Sizes: {p['size']}")
            print(f"Color: {p['color']}")
            print(f"Price: {p['price']}")
            print(f"Image: {p['img_url']}")
            print(f"Ref item: {p['ref_item']}")
            print(f"Shop ID: {p['shop_id']}")
            print(f"Sex: {p['sex']}")
            print(f"URL: {p['url']}")


if __name__ == "__main__":
    main()
