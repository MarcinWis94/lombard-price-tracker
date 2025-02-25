import sqlite3
import datetime
import hashlib  # Do generowania unikalnego produkt_id
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# Konfiguracja Selenium
options = Options()
options.add_argument("--headless")  # Tryb bez interfejsu
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

# Uruchomienie przeglądarki
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# Połączenie z bazą danych
conn = sqlite3.connect("loombard_products.db")
cursor = conn.cursor()

# Tworzenie tabeli 'produkty'
cursor.execute("""
CREATE TABLE IF NOT EXISTS produkty (
    produkt_id TEXT PRIMARY KEY, 
    nazwa TEXT,
    cena TEXT,
    lokalizacja TEXT,
    stan TEXT,
    link TEXT,
    kategoria TEXT,
    data_pobrania TEXT
)
""")

# Tworzenie tabeli 'historia_cen'
cursor.execute("""
CREATE TABLE IF NOT EXISTS historia_cen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    produkt_id TEXT,
    cena TEXT,
    data_zmiany TEXT,
    FOREIGN KEY (produkt_id) REFERENCES produkty(produkt_id)
)
""")
conn.commit()

# Lista kategorii do przeszukania
categories = {
    "RTV i AGD": "https://www.loombard.pl/categories/rtv-i-agd-j9WGej?",
    "Laptopy": "https://www.loombard.pl/categories/laptopy-iPpDk9?",
    "Głośniki": "https://www.loombard.pl/categories/glosniki-9MhYyr?",
    "Aparaty cyfrowe": "https://www.loombard.pl/categories/aparaty-cyfrowe-oEc6i6?",
    "Konsole i automaty": "https://www.loombard.pl/categories/konsole-i-automaty-iLQlqa?",
    "Smartfony": "https://www.loombard.pl/categories/smartfony-i-telefony-komorkowe-WDK5Fy?",
    "Smartwatche": "https://www.loombard.pl/categories/smartwatche-Z9ALnj?"
}

today = datetime.date.today().strftime("%Y-%m-%d")  # Dzisiejsza data

added_products = []  # Lista dodanych produktów
updated_prices = []  # Lista produktów zaktualizowanych cen

for category_name, base_url in categories.items():
    print(f"\n🔍 Przeszukuję kategorię: {category_name}")
    page = 1

    while True:
        url = f"{base_url}page={page}"
        print(f"🗄 Pobieram stronę {page}: {url}")

        driver.get(url)
        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, "html.parser")

        products = soup.find_all("div", class_="product-item")
        if not products:
            print("❌ Brak więcej produktów, przechodzę do następnej kategorii.")
            break

        for product in products:
            title_tag = product.find("h2", class_="product-title")
            name = title_tag.text.strip() if title_tag else "Brak nazwy"

            price_tag = product.find("p", class_="product-value")
            price = price_tag.text.strip() if price_tag else "Brak ceny"

            link_tag = title_tag.find("a") if title_tag else None
            link = "https://www.loombard.pl" + link_tag["href"] if link_tag else "Brak linku"

            location_tag = product.find("p", class_="product-desc")
            location = location_tag.text.strip().replace("Lokalizacja: ", "") if location_tag else "Brak lokalizacji"

            condition_tag = product.find_all("p", class_="product-desc")
            condition = condition_tag[1].text.strip().replace("Stan: ", "") if len(condition_tag) > 1 else "Brak stanu"

            product_id_source = name + location + link  # Dodanie linku do identyfikatora
            product_id = hashlib.md5(product_id_source.encode()).hexdigest()

            cursor.execute("SELECT cena FROM produkty WHERE produkt_id = ?", (product_id,))
            existing_product = cursor.fetchone()

            if existing_product:
                existing_price = existing_product[0]

                if existing_price != price:
                    cursor.execute("""
                    INSERT INTO historia_cen (produkt_id, cena, data_zmiany) 
                    VALUES (?, ?, ?)
                    """, (product_id, existing_price, today))

                    cursor.execute("""
                    UPDATE produkty SET cena = ?, data_pobrania = ? WHERE produkt_id = ?
                    """, (price, today, product_id))

                    updated_prices.append(name)
                    print(f"♻️ Cena zmieniła się dla {name}! Poprzednia cena: {existing_price} → Nowa: {price}")
                else:
                    print(f"✅ Cena produktu {name} się nie zmieniła.")
            else:
                cursor.execute("""
                INSERT INTO produkty (produkt_id, nazwa, cena, lokalizacja, stan, link, kategoria, data_pobrania) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (product_id, name, price, location, condition, link, category_name, today))

                added_products.append(name)
                print(f"➕ Dodano nowy produkt: {name}")

        conn.commit()
        print(f"🔍 Znaleziono {len(products)} produktów na stronie {page}.")
        page += 1

driver.quit()
conn.close()

print("\n📢 Podsumowanie:")
if added_products:
    print(f"🆕 Dodano {len(added_products)} nowych produktów:")
    for product in added_products:
        print(f"  - {product}")
if updated_prices:
    print(f"📉 Zaktualizowano ceny dla {len(updated_prices)} produktów:")
    for product in updated_prices:
        print(f"  - {product}")
print("💾 Dane zostały zapisane do bazy danych!")
