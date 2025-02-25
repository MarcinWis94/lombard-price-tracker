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

# Główna kategoria elektroniki
base_url = "https://www.loombard.pl/categories/elektronika-MDn0gF"
MAX_PAGES = 3  # Pobieramy tylko 3 strony
page = 1
all_products = []

while page <= MAX_PAGES:
    url = f"{base_url}?page={page}"
    print(f"\U0001F4C4 Pobieram stronę {page}: {url}")

    # Otwieramy stronę i czekamy na załadowanie JS
    driver.get(url)
    time.sleep(3)

    # Pobieramy HTML
    soup = BeautifulSoup(driver.page_source, "html.parser")

    # Znalezienie wszystkich produktów
    products = soup.find_all("div", class_="product-item")

    if not products:
        print("❌ Brak więcej produktów, kończę.")
        break

    # Pobieranie danych z każdego produktu
    for product in products:
        title_tag = product.find("h2", class_="product-title")
        name = title_tag.text.strip() if title_tag else "Brak nazwy"

        price_tag = product.find("p", class_="product-value")
        price = price_tag.text.strip() if price_tag else "Brak ceny"

        link_tag = title_tag.find("a") if title_tag else None
        link = "https://www.loombard.pl" + link_tag["href"] if link_tag else "Brak linku"

        all_products.append((name, price, link))

    print(f"\U0001F50D Znaleziono {len(products)} produktów na stronie {page}.")
    page += 1  # Przechodzimy do następnej strony

# Zatrzymujemy Selenium
driver.quit()

# Wyświetlamy wyniki
for product in all_products:
    print(f"Nazwa: {product[0]}, Cena: {product[1]}, Link: {product[2]}")
