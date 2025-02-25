import sqlite3
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

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

# Tworzenie tabeli, jeśli nie istnieje
cursor.execute("""
CREATE TABLE IF NOT EXISTS produkty (
    nazwa TEXT PRIMARY KEY,
    cena TEXT,
    lokalizacja TEXT,
    stan TEXT,
    kategoria TEXT,
    link TEXT
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

            # Zapisywanie danych do bazy danych z informacją o kategorii
            cursor.execute("""
            INSERT OR REPLACE INTO produkty (nazwa, cena, lokalizacja, stan, link, kategoria) 
            VALUES (?, ?, ?, ?, ?, ?)
            """, (name, price, location, condition, link, category_name))

        conn.commit()  # Zapisujemy zmiany do bazy
        print(f"\U0001F50D Znaleziono {len(products)} produktów na stronie {page}.")

# Zatrzymujemy Selenium i zamykamy połączenie z bazą
driver.quit()
conn.close()

print("\U0001F4BE Dane zostały zapisane do bazy danych!")
