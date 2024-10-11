import json
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# List of categories and their URLs for scraping Albert's website
albert_urls = [
    {"max_page_urls": "https://www.albert.cz/shop/Napoje/c/zeM001?pageNumber=15", "cat": "nápoje"},
    {"max_page_urls": "https://www.albert.cz/shop/Maso-a-ryby/c/zeH001?pageNumber=8", "cat": "maso a ryby"},
    {"max_page_urls": "https://www.albert.cz/shop/Uzeniny-a-lahudky/c/zeK001?pageNumber=22",
     "cat": "uzeniny a lahůdky"},
    {"max_page_urls": "https://www.albert.cz/shop/Mrazene/c/zeJ005?pageNumber=15", "cat": "mražené"},
    {"max_page_urls": "https://www.albert.cz/shop/Specialni-vyziva/c/zeN001?pageNumber=24", "cat": "speciální výživa"},
    {"max_page_urls": "https://www.albert.cz/shop/Drogerie-a-kosmetika/c/zeQ001?pageNumber=94",
     "cat": "drogerie a kosmetika"},
    {"max_page_urls": "https://www.albert.cz/shop/Dite/c/zeP001?pageNumber=34", "cat": "dítě"},
    {"max_page_urls": "https://www.albert.cz/shop/Domacnost-a-zahrada/c/zeS001?pageNumber=29",
     "cat": "domácnost a zahrada"},
    {"max_page_urls": "https://www.albert.cz/shop/Zvirata/c/zeR001?pageNumber=17", "cat": "zvířata"},
    {"max_page_urls": "https://www.albert.cz/shop/Ovoce-a-zelenina/c/zeG001?pageNumber=19", "cat": "ovoce a zelenina"},
    {"max_page_urls": "https://www.albert.cz/shop/Mlecne-a-chlazene/c/zeJ001?pageNumber=64",
     "cat": "mléčné a chlazené"},
    {"max_page_urls": "https://www.albert.cz/shop/Pekarna-a-cukrarna/c/zeF001?pageNumber=13",
     "cat": "pekárna a cukrárna"},
    {"max_page_urls": "https://www.albert.cz/shop/Trvanlive/c/zeL001?pageNumber=150", "cat": "trvanlivé"}
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

    # Select page elements containing product data
    item_elements = driver.find_elements(By.XPATH, "//a[@data-testid='product-block-name-link']")
    actual_price_elements = driver.find_elements(By.XPATH,
                                                 "//div[@data-testid='product-block-price']//div[@class='sc-dqia0p-9 dsNELN']")
    actual_price_sup_elements = driver.find_elements(By.XPATH,
                                                     "//div[@data-testid='product-block-price']//sup[@class='sc-dqia0p-10 fjOrrj']")
    old_price_elements = driver.find_elements(By.XPATH, "//span[@data-testid='product-block-old-price']")

    print(
        f"Found {len(item_elements)} items, {len(actual_price_elements)} prices, and {len(old_price_elements)} old prices.")

    items = []
    for i, item_elem in enumerate(item_elements):
        item_name = item_elem.get_attribute('title')
        item_url = item_elem.get_attribute('href')

        # Handle cases where the item name is missing
        if not item_name and item_url:
            item_name_raw = item_url.split('/')[-3] if len(item_url.split('/')) >= 3 else ''
            item_name = ' '.join(item_name_raw.split('-')).capitalize()

        actual_price = actual_price_elements[i].text.strip() if i < len(actual_price_elements) else ""
        actual_price_sup = actual_price_sup_elements[i].text.strip() if i < len(actual_price_sup_elements) else ""
        full_price = f"{actual_price},{actual_price_sup} Kč" if actual_price and actual_price_sup else ""

        old_price = old_price_elements[i].text.strip() if i < len(old_price_elements) else None

        # Debug print for each product
        print(
            f"Item {i + 1}: Name='{item_name}', URL='{item_url}', Actual Price='{full_price}', Old Price='{old_price}'")

        items.append({
            'name': item_name,
            'url': item_url,
            'category': category,
            'actual_price': full_price,
            'old_price': old_price
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


def scrape_albert_pages(albert_urls, output_file):
    """
    Scrape all pages for each category in the albert_urls list and save results to a JSON file.

    :param albert_urls: List of dictionaries with URLs and categories to scrape.
    :param output_file: The file path to save the scraped data.
    """
    driver = initialize_driver()
    try:
        for category_data in albert_urls:
            base_url = category_data['max_page_urls']
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
    output_file = "albert_items.json"
    scrape_albert_pages(albert_urls, output_file)
    print(f"Scraping complete! Data saved to '{output_file}'.")
