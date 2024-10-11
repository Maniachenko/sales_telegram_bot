import json
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# List of URLs for Tesco categories
tesco_urls = [
    {'url': 'https://nakup.itesco.cz/groceries/cs-CZ/promotions/all?superdepartment=28429&page=1', 'cat': 'péče o domácnost', 'pages': 26},
    {'url': 'https://nakup.itesco.cz/groceries/cs-CZ/promotions/all?superdepartment=28069&page=1', 'cat': 'nápoje', 'pages': 17},
    {'url': 'https://nakup.itesco.cz/groceries/cs-CZ/promotions/all?superdepartment=27122&page=1', 'cat': 'alkoholické nápoje', 'pages': 20},
    {'url': 'https://nakup.itesco.cz/groceries/cs-CZ/promotions/all?superdepartment=27294&page=1', 'cat': 'chovatelské potřeby', 'pages': 14},
    {'url': 'https://nakup.itesco.cz/groceries/cs-CZ/promotions/all?superdepartment=28537&page=1', 'cat': 'péče o děti', 'pages': 12},
    {'url': 'https://nakup.itesco.cz/groceries/cs-CZ/promotions/all?superdepartment=27874&page=1', 'cat': 'mléčné výrobky, vejce, margaríny a výrobky ke šlehání', 'pages': 9},
    {'url': 'https://nakup.itesco.cz/groceries/cs-CZ/promotions/all?superdepartment=28609&page=1', 'cat': 'speciální výživa', 'pages': 8},
    {'url': 'https://nakup.itesco.cz/groceries/cs-CZ/promotions/all?superdepartment=27340&page=1', 'cat': 'domov a zábava', 'pages': 5},
    {'url': 'https://nakup.itesco.cz/groceries/cs-CZ/promotions/all?superdepartment=28283&page=1', 'cat': 'ovoce a zelenina', 'pages': 3},
    {'url': 'https://nakup.itesco.cz/groceries/cs-CZ/promotions/all?superdepartment=27766&page=1', 'cat': 'maso, ryby a lahůdky', 'pages': 3},
    {'url': 'https://nakup.itesco.cz/groceries/cs-CZ/promotions/all?superdepartment=28010&page=1', 'cat': 'mražené potraviny', 'pages': 2},
    {'url': 'https://nakup.itesco.cz/groceries/cs-CZ/promotions/all?superdepartment=28377&page=1', 'cat': 'pekárna a cukrárna', 'pages': 2},
    {'url': 'https://nakup.itesco.cz/groceries/cs-CZ/promotions/all?superdepartment=27572&page=1', 'cat': 'drogerie a kosmetika', 'pages': 50},
    {'url': 'https://nakup.itesco.cz/groceries/cs-CZ/promotions/all?superdepartment=28724&page=1', 'cat': 'trvanlivé potraviny', 'pages': 47},
]

# Function to initialize the Chrome WebDriver
def initialize_driver():
    """
    Initialize the Chrome WebDriver for web scraping.

    :return: A Selenium WebDriver instance with headless Chrome.
    """
    options = Options()
    options.headless = True  # Run Chrome in headless mode (no GUI)
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    return driver

# Scrape a single page using Selenium
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
    time.sleep(2)  # Wait for the page to load

    # Find product names and URLs using XPath
    item_elements = driver.find_elements(By.XPATH, "//h3/a/span")
    item_links = driver.find_elements(By.XPATH, "//h3/a[@class='styled__Anchor-sc-1i711qa-0 hXcydL ddsweb-link__anchor']")

    items = []
    for item_elem, link_elem in zip(item_elements, item_links):
        item_name = item_elem.text.strip()
        item_url = link_elem.get_attribute('href')
        items.append({'name': item_name, 'url': item_url, 'category': category})

    return items

# Function to append scraped items to a JSON file
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

    # Append new items to existing item_names
    existing_data.extend(items)

    # Write updated item_names back to the file
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=4)

# Function to iterate through all pages for each category
def scrape_tesco_pages(tesco_urls, output_file):
    """
    Scrape all pages for each category in the tesco_urls list and save results to a JSON file.

    :param tesco_urls: List of dictionaries with URLs and categories to scrape.
    :param output_file: The file path to save the scraped data.
    """
    driver = initialize_driver()  # Start the browser
    try:
        for category_data in tesco_urls:
            base_url = category_data['url']
            category = category_data['cat']
            total_pages = category_data['pages']

            for page in range(1, total_pages + 1):
                page_url = base_url.replace('page=1', f'page={page}')
                items_on_page = scrape_page(driver, page_url, category)

                # Append the items to the JSON file after scraping each page
                append_to_json_file(output_file, items_on_page)

                # Sleep to avoid overwhelming the server
                time.sleep(2)

    finally:
        driver.quit()  # Close the browser once scraping is complete

# Main script
if __name__ == "__main__":
    output_file = "tesco_items.json"

    # Scrape all items from the given URLs and update the JSON file after each page
    scrape_tesco_pages(tesco_urls, output_file)

    print(f"Scraping complete! Data incrementally saved to '{output_file}'.")
