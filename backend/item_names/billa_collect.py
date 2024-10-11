import json
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# List of categories and URLs for scraping BILLA's website
billa_urls = [
    {"max_page_url": "https://shop.billa.cz/produkty/ovoce-a-zelenina-1165?page=16", "cat": "ovoce a zelenina"},
    {"max_page_url": "https://shop.billa.cz/produkty/pecivo-1198?page=16", "cat": "pečivo"},
    {"max_page_url": "https://shop.billa.cz/produkty/chlazene-mlecne-a-rostlinne-vyrobky-1207?page=16",
     "cat": "chlazené, mléčné a rostlinné výrobky"},
    {"max_page_url": "https://shop.billa.cz/produkty/maso-a-ryby-1263?page=16", "cat": "maso a ryby"},
    {"max_page_url": "https://shop.billa.cz/produkty/uzeniny-lahudky-a-hotova-jidla-1276?page=16",
     "cat": "uzeniny, lahůdky a hotová jídla"},
    {"max_page_url": "https://shop.billa.cz/produkty/mrazene-1307?page=16", "cat": "mražené"},
    {"max_page_url": "https://shop.billa.cz/produkty/trvanlive-potraviny-1332?page=16", "cat": "trvanlivé potraviny"},
    {"max_page_url": "https://shop.billa.cz/produkty/cukrovinky-1449?page=16", "cat": "cukrovinky"},
    {"max_page_url": "https://shop.billa.cz/produkty/napoje-1474?page=16", "cat": "nápoje"},
    {"max_page_url": "https://shop.billa.cz/produkty/specialni-a-rostlinna-vyziva-1576?page=16",
     "cat": "speciální a rostlinná výživa"},
    {"max_page_url": "https://shop.billa.cz/produkty/pece-o-dite-1582?page=16", "cat": "péče o dítě"},
    {"max_page_url": "https://shop.billa.cz/produkty/drogerie-a-kosmetika-2426?page=16", "cat": "drogerie a kosmetika"},
    {"max_page_url": "https://shop.billa.cz/produkty/domacnost-2427?page=16", "cat": "domácnost"},
    {"max_page_url": "https://shop.billa.cz/produkty/mazlicci-1630?page=16", "cat": "mazlíčci"},
    {"max_page_url": "https://shop.billa.cz/produkty/billa-vlastni-vyroba-2030", "cat": "BILLA Vlastní výroba"},
    {"max_page_url": "https://shop.billa.cz/produkty/billa-regionalne-1667?page=16", "cat": "BILLA Regionálně"}
]


def initialize_driver():
    """
    Initialize the Chrome WebDriver for web scraping.

    :return: A Selenium WebDriver instance with headless Chrome.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
    return driver


def scroll_to_bottom(driver):
    """
    Scroll down the webpage until no new content is loaded.

    :param driver: The Selenium WebDriver instance.
    """
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)  # Wait for new content to load
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


def scrape_page(driver, url, category):
    """
    Scrape product data from a single page.

    :param driver: The Selenium WebDriver instance.
    :param url: The URL of the page to scrape.
    :param category: The product category being scraped.
    :return: A list of dictionaries with product details.
    """
    print(f"Scraping URL: {url} for category: {category}")
    driver.get(url)
    time.sleep(5)  # Allow the page to fully load

    # Scroll to load all dynamic content
    scroll_to_bottom(driver)

    # Select elements containing product data
    item_name_elements = driver.find_elements(By.XPATH, "//h3[@data-test='product-title']//span")

    print(f"Found {len(item_name_elements)} items.")

    items = []
    for i, item_elem in enumerate(item_name_elements):
        item_name = item_elem.text.strip()

        # Debug print for each product
        print(f"Item {i + 1}: Name='{item_name}'")

        items.append({
            'name': item_name,
            'category': category
        })

    return items


def append_to_json_file(filename, items):
    """
    Append scraped items to a JSON file.

    :param filename: The path of the JSON file to update.
    :param items: List of items to append.
    """
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
    else:
        existing_data = []

    # Append new items and save back to the file
    existing_data.extend(items)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=4)


def scrape_billa_pages(billa_urls, output_file):
    """
    Scrape all pages for each category in the billa_urls list and save results to a JSON file.

    :param billa_urls: List of dictionaries with URLs and categories to scrape.
    :param output_file: The file path to save the scraped data.
    """
    driver = initialize_driver()
    try:
        for category_data in billa_urls:
            base_url = category_data['max_page_url']
            category = category_data['cat']

            # Scrape items on the current page
            items_on_page = scrape_page(driver, base_url, category)

            # Append scraped items to the JSON file
            append_to_json_file(output_file, items_on_page)

            # Sleep to avoid overwhelming the server
            time.sleep(2)

    finally:
        driver.quit()  # Ensure the driver is properly closed


# Main script
if __name__ == "__main__":
    output_file = "billa_items.json"

    # Scrape all items from the given URLs and update the JSON file after each page
    scrape_billa_pages(billa_urls, output_file)

    print(f"Scraping complete! Data incrementally saved to '{output_file}'.")
