import sqlite3
import datetime
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import hashlib  # Do generowania unikalnego produkt_id

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

# Tworzenie tabeli (z nową kolumną historia_cen)
cursor.execute("""
CREATE TABLE IF NOT EXISTS produkty (
    produkt_id TEXT PRIMARY KEY, 
    nazwa TEXT,
    cena TEXT,
    historia_cen TEXT DEFAULT '{}',
    lokalizacja TEXT,
    stan TEXT,
    link TEXT,
    kategoria TEXT,
    data_pobrania TEXT
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

MAX_PAGES = 3  # Liczba stron do przeszukania
today = datetime.date.today().strftime("%Y-%m-%d")  # Dzisiejsza data
current_week = datetime.date.today().isocalendar()[1]  # Numer tygodnia

for category_name, base_url in categories.items():
    print(f"\n🔍 Przeszukuję kategorię: {category_name}")

    for page in range(1, MAX_PAGES + 1):
        url = f"{base_url}page={page}"
        print(f"\U0001F4C4 Pobieram stronę {page}: {url}")

        # Otwieramy stronę i czekamy na załadowanie JS
        driver.get(url)
        time.sleep(3)

        # Pobieramy HTML
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Znalezienie wszystkich produktów
        products = soup.find_all("div", class_="product-item")

        if not products:
            print("❌ Brak więcej produktów, przechodzę do następnej kategorii.")
            break

        # Pobieranie danych z każdego produktu
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

            # Generowanie unikalnego produkt_id na podstawie nazwy i lokalizacji
            product_id = hashlib.md5((name + location).encode()).hexdigest()

            # Sprawdzenie, czy produkt już istnieje
            cursor.execute("SELECT cena, historia_cen FROM produkty WHERE produkt_id = ?", (product_id,))
            existing_product = cursor.fetchone()

            if existing_product:
                existing_price, price_history_json = existing_product

                # Konwersja historii cen z JSON do słownika
                price_history = json.loads(price_history_json) if price_history_json else {}

                if existing_price == price:
                    print(f"✅ Cena produktu {name} się nie zmieniła.")
                else:
                    # Sprawdzenie, czy cena zmienia się w nowym tygodniu
                    last_week = max([int(week) for week in price_history.keys()], default=0)
                    if current_week > last_week:
                        price_history[str(current_week)] = existing_price
                        updated_price_history_json = json.dumps(price_history)

                        # Aktualizacja wpisu
                        cursor.execute("""
                        UPDATE produkty SET cena = ?, historia_cen = ?, data_pobrania = ? WHERE produkt_id = ?
                        """, (price, updated_price_history_json, today, product_id))

                        print(f"♻️ Cena zmieniła się dla {name}! Poprzednia cena: {existing_price} → Nowa: {price}")
                    else:
                        # Aktualizacja tylko ceny i daty pobrania
                        cursor.execute("""
                        UPDATE produkty SET cena = ?, data_pobrania = ? WHERE produkt_id = ?
                        """, (price, today, product_id))
                        print(f"🔄 Cena zaktualizowana w tym samym tygodniu: {name}")

            else:
                # Nowy produkt - dodajemy do bazy
                initial_price_history = json.dumps({})  # Pusta historia cen
                cursor.execute("""
                INSERT INTO produkty (produkt_id, nazwa, cena, historia_cen, lokalizacja, stan, link, kategoria, data_pobrania) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (product_id, name, price, initial_price_history, location, condition, link, category_name, today))
                print(f"➕ Dodano nowy produkt: {name}")

        conn.commit()  # Zapisujemy zmiany do bazy
        print(f"\U0001F50D Znaleziono {len(products)} produktów na stronie {page}.")

# Zatrzymujemy Selenium i zamykamy połączenie z bazą
driver.quit()
conn.close()

print("\U0001F4BE Dane zostały zapisane do bazy danych!")
