import time
import hashlib
import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import sqlite3

# ======================
# Klasa Database
# ======================
class Database:
    def __init__(self, db_path="loombard_products.db"):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # Tabela produktów
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS produkty (
            produkt_id TEXT PRIMARY KEY,
            nazwa TEXT,
            lokalizacja TEXT,
            stan TEXT,
            link TEXT,
            kategoria TEXT
        )
        """)
        # Tabela cen (historia)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS ceny (
            produkt_id TEXT,
            cena REAL,
            data_pobrania TEXT,
            FOREIGN KEY (produkt_id) REFERENCES produkty(produkt_id)
        )
        """)
        self.conn.commit()

    def add_product(self, nazwa, lokalizacja, stan, link, kategoria):
        """
        Dodaje produkt do tabeli produkty, jeśli go nie ma.
        Zwraca produkt_id.
        """
        produkt_id_source = nazwa + lokalizacja + link
        produkt_id = hashlib.md5(produkt_id_source.encode()).hexdigest()

        self.cursor.execute("SELECT 1 FROM produkty WHERE produkt_id = ?", (produkt_id,))
        exists = self.cursor.fetchone()

        if not exists:
            self.cursor.execute("""
            INSERT INTO produkty (produkt_id, nazwa, lokalizacja, stan, link, kategoria)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (produkt_id, nazwa, lokalizacja, stan, link, kategoria))
            print(f"➕ Dodano nowy produkt: {nazwa}")
            self.conn.commit()
        else:
            print(f"🔁 Produkt już istnieje: {nazwa}")

        return produkt_id

    def add_price(self, produkt_id, cena):
        """
        Dodaje nową cenę do tabeli ceny za każdym razem.
        """
        today = datetime.date.today().strftime("%Y-%m-%d")
        self.cursor.execute("""
        INSERT INTO ceny (produkt_id, cena, data_pobrania)
        VALUES (?, ?, ?)
        """, (produkt_id, cena, today))
        print(f"💰 Dodano nową cenę: {cena} dla produktu_id={produkt_id}")
        self.conn.commit()

    def close(self):
        self.conn.close()


# ======================
# Funkcje scraperowe
# ======================
def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def scrape_category(driver, db, category_name, base_url):
    page = 1
    while True:
        url = f"{base_url}page={page}"
        print(f"\n🗄 Pobieram stronę {page}: {url}")
        driver.get(url)
        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        products = soup.find_all("div", class_="product-item")
        if not products:
            print("❌ Brak więcej produktów w tej kategorii.")
            break

        for product in products:
            # Nazwa
            title_tag = product.find("h2", class_="product-title")
            name = title_tag.text.strip() if title_tag else "Brak nazwy"

            # Cena
            price_tag = product.find("p", class_="product-value")
            price_text = price_tag.text.strip() if price_tag else "0"
            try:
                cena = float(price_text.replace("zł", "").replace(",", ".").replace(" ", ""))
            except:
                cena = 0.0

            # Link
            link_tag = title_tag.find("a") if title_tag else None
            link = "https://www.loombard.pl" + link_tag["href"] if link_tag else "Brak linku"

            # Lokalizacja
            location_tag = product.find("p", class_="product-desc")
            location = location_tag.text.strip().replace("Lokalizacja: ", "") if location_tag else "Brak lokalizacji"

            # Stan
            condition_tag = product.find_all("p", class_="product-desc")
            stan = condition_tag[1].text.strip().replace("Stan: ", "") if len(condition_tag) > 1 else "Brak stanu"

            # Dodaj produkt i cenę
            produkt_id = db.add_product(name, location, stan, link, category_name)
            db.add_price(produkt_id, cena)

        page += 1

# ======================
# Główna logika
# ======================
def main():
    categories = {
        "RTV i AGD": "https://www.loombard.pl/categories/rtv-i-agd-j9WGej?",
        "Laptopy": "https://www.loombard.pl/categories/laptopy-iPpDk9?",
        "Głośniki": "https://www.loombard.pl/categories/glosniki-9MhYyr?",
        "Aparaty cyfrowe": "https://www.loombard.pl/categories/aparaty-cyfrowe-oEc6i6?",
        "Konsole i automaty": "https://www.loombard.pl/categories/konsole-i-automaty-iLQlqa?",
        "Smartfony": "https://www.loombard.pl/categories/smartfony-i-telefony-komorkowe-WDK5Fy?",
        "Smartwatche": "https://www.loombard.pl/categories/smartwatche-Z9ALnj?"
    }

    db = Database()
    driver = get_driver()

    for category_name, base_url in categories.items():
        print(f"\n🔍 Przeszukuję kategorię: {category_name}")
        scrape_category(driver, db, category_name, base_url)

    driver.quit()
    db.close()
    print("\n💾 Scraping zakończony, wszystkie dane zapisane w bazie!")

# ======================
# Uruchomienie
# ======================
if __name__ == "__main__":
    main()
