import json
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Globus URLs with maximum page numbers
globus_urls = [
    {"max_page_url": "https://shop.iglobus.cz/cz/pek%C3%A1rna-a-cukr%C3%A1rna?page=20#", "cat": "pekárna a cukrárna"},
    {"max_page_url": "https://shop.iglobus.cz/cz/maso-a-ryby?ipp=24&page=5#", "cat": "maso a ryby"},
    {"max_page_url": "https://shop.iglobus.cz/cz/ovoce-a-zelenina?ipp=24&page=11#", "cat": "ovoce a zelenina"},
    {"max_page_url": "https://shop.iglobus.cz/cz/ml%C3%A9%C4%8Dn%C3%A9-a-chlazen%C3%A9?ipp=24&page=69#",
     "cat": "mléčné a chlazené"},
    {"max_page_url": "https://shop.iglobus.cz/cz/trvanliv%C3%A9-potraviny?ipp=24&page=218#",
     "cat": "trvanlivé potraviny"},
    {"max_page_url": "https://shop.iglobus.cz/cz/mra%C5%BEen%C3%A9-potraviny?ipp=24&page=26#",
     "cat": "mražené potraviny"},
    {"max_page_url": "https://shop.iglobus.cz/cz/n%C3%A1poje?ipp=24&page=131#", "cat": "nápoje"},
    {"max_page_url": "https://shop.iglobus.cz/cz/drogerie-a-kosmetika?ipp=24&page=191#", "cat": "drogerie a kosmetika"},
    {"max_page_url": "https://shop.iglobus.cz/cz/sv%C4%9Bt-d%C4%9Bt%C3%AD?ipp=24&page=90#", "cat": "svět dětí"}
]


def initialize_driver():
    """
    Initialize the Chrome WebDriver for web scraping.

    :return: A Selenium WebDriver instance with headless Chrome.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
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
        time.sleep(2)  # Wait for new content to load
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

    # Scroll down to load all dynamic content
    scroll_to_bottom(driver)

    # Locate the product blocks using CSS selectors
    product_blocks = driver.find_elements(By.CSS_SELECTOR, "div.product-item__info")

    print(f"Found {len(product_blocks)} products.")

    items = []
    for i, block in enumerate(product_blocks):
        # Extract the product name
        try:
            item_name_elem = block.find_element(By.CSS_SELECTOR, "a.product-item__name-cz")
            item_name = item_name_elem.text.strip()
            item_url = "https://shop.iglobus.cz" + \
                       item_name_elem.get_attribute('onclick').split("productClicked('")[1].split("',")[0]
        except Exception as e:
            print(f"Error extracting item name or URL: {e}")
            item_name, item_url = '', ''

        # Extract actual price
        try:
            price_script = block.get_attribute('onclick')
            actual_price = price_script.split("', '")[3]
        except Exception as e:
            print(f"Error extracting actual price: {e}")
            actual_price = ''

        # Debug print each item info
        print(f"Item {i + 1}: Name='{item_name}', URL='{item_url}', Actual Price='{actual_price}'")

        items.append({
            'name': item_name,
            'url': item_url,
            'category': category,
            'actual_price': actual_price,
            'old_price': None  # Globus doesn't seem to have old prices in this structure
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


def scrape_globus_pages(globus_urls, output_file):
    """
    Scrape all pages for each category in the globus_urls list and save results to a JSON file.

    :param globus_urls: List of dictionaries with URLs and categories to scrape.
    :param output_file: The file path to save the scraped data.
    """
    driver = initialize_driver()  # Start the browser
    try:
        for category_data in globus_urls:
            base_url = category_data['max_page_url']
            category = category_data['cat']

            # Extract max page number from the URL
            max_page_num = int(base_url.split('page=')[1].split('#')[0])

            # Iterate through all pages for the current category
            for page in range(1, max_page_num + 1):
                page_url = base_url.replace(f'page={max_page_num}', f'page={page}')
                items_on_page = scrape_page(driver, page_url, category)

                # Append the items to the JSON file after scraping each page
                append_to_json_file(output_file, items_on_page)

                # Sleep to avoid overwhelming the server
                time.sleep(2)

    finally:
        driver.quit()  # Close the browser once scraping is complete


# Main script
if __name__ == "__main__":
    output_file = "globus_items.json"

    # Scrape all items from the given URLs and update the JSON file after each page
    scrape_globus_pages(globus_urls, output_file)

    print(f"Scraping complete! Data incrementally saved to '{output_file}'.")
