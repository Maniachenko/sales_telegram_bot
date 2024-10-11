import json
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# List of URLs for Penny categories
penny_urls = [
    {"url": "https://www.penny.cz/category/ovoce-a-zelenina-16", "cat": "ovoce a zelenina"},
    {"url": "https://www.penny.cz/category/maso-a-uzeniny-19", "cat": "maso a uzeniny"},
    {"url": "https://www.penny.cz/category/chlazene-vyrobky-20", "cat": "chlazene vyrobky"},
    {"url": "https://www.penny.cz/category/chleb-a-pecivo-21", "cat": "chléb a pečivo"},
    {"url": "https://www.penny.cz/category/mrazene-vyrobky-22", "cat": "mražené"},
    {"url": "https://www.penny.cz/category/napoje-23", "cat": "nápoje"},
    {"url": "https://www.penny.cz/category/alkohol-24", "cat": "alkohol"},
    {"url": "https://www.penny.cz/category/potraviny-25", "cat": "potraviny"},
    {"url": "https://www.penny.cz/category/kava-caj-kakao-26", "cat": "káva, čaj, kakao"},
    {"url": "https://www.penny.cz/category/cukrovinky-27", "cat": "cukrovinky"},
    {"url": "https://www.penny.cz/category/pro-zvirata-29", "cat": "pro zvířata"},
    {"url": "https://www.penny.cz/category/drogerie-30", "cat": "drogerie"}
]


# Function to initialize the Chrome WebDriver
def initialize_driver():
    """
    Initialize the Chrome WebDriver for web scraping.

    :return: A Selenium WebDriver instance with headless Chrome.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode to avoid GUI
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
    return driver


# Function to scroll down the page until no new content is loaded
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


# Function to scrape item names from a single page with explicit wait
def scrape_page(driver, url, category):
    """
    Scrape product names from a single page.

    :param driver: The Selenium WebDriver instance.
    :param url: The URL of the page to scrape.
    :param category: The product category being scraped.
    :return: A list of dictionaries with product details.
    """
    print(f"Scraping URL: {url} for category: {category}")
    driver.get(url)
    time.sleep(5)  # Wait for the page to load

    # Scroll down to load all dynamic content
    scroll_to_bottom(driver)

    # Explicit wait to ensure the product tiles are present
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, "//button[@item_names-test='product-tile-link']/span"))
    )

    # Find item name elements on the page
    item_name_elements = driver.find_elements(By.XPATH, "//button[@item_names-test='product-tile-link']/span")

    print(f"Found {len(item_name_elements)} items.")

    items = []
    for i, item_elem in enumerate(item_name_elements):
        # Retrieve the text inside the span element
        item_name = item_elem.get_attribute('textContent').strip()

        # Debugging in case of empty names
        if not item_name:
            print(f"Item {i + 1}: Outer HTML: {item_elem.get_attribute('outerHTML')}")

        # Print the item info for debugging
        print(f"Item {i + 1}: Name='{item_name}'")

        # Append the item info to the list
        items.append({
            'name': item_name if item_name else "No Name Found",  # Handle empty names gracefully
            'category': category
        })

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

    # Append new items and save back to the file
    existing_data.extend(items)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=4)


# Function to iterate through all pages for each category
def scrape_penny_pages(penny_urls, output_file):
    """
    Scrape all pages for each category in the penny_urls list and save results to a JSON file.

    :param penny_urls: List of dictionaries with URLs and categories to scrape.
    :param output_file: The file path to save the scraped data.
    """
    driver = initialize_driver()  # Start the browser
    try:
        for category_data in penny_urls:
            base_url = category_data['url']
            category = category_data['cat']

            # Scrape the entire page content by scrolling to the bottom
            items_on_page = scrape_page(driver, base_url, category)

            # Append the items to the JSON file after scraping each category page
            append_to_json_file(output_file, items_on_page)

            # Sleep to avoid overwhelming the server
            time.sleep(2)

    finally:
        driver.quit()  # Close the browser once scraping is complete


# Main script
if __name__ == "__main__":
    output_file = "penny_items.json"

    # Scrape all items from the given URLs and update the JSON file after each page
    scrape_penny_pages(penny_urls, output_file)

    print(f"Scraping complete! Data incrementally saved to '{output_file}'.")
