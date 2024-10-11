import requests
from bs4 import BeautifulSoup
import json
import time

# Load the products JSON file
with open('item_names/akcniceny_items.json', 'r', encoding='utf-8') as f:
    products = json.load(f)


# Function to scrape product category from a given product link
def scrape_category(product_link):
    try:
        response = requests.get(product_link)
        response.raise_for_status()  # Ensure a successful request
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the category element
        category_element = soup.select_one('span[itemprop="category"]')

        if category_element:
            # Extract all category names as a string
            categories = " / ".join([cat.get_text() for cat in category_element.find_all('a')])
            return categories
        return None
    except requests.RequestException as e:
        print(f"Error scraping {product_link}: {e}")
        return 'Unknown'


# Scrape categories for all products, updating the file after each iteration
for index, product in enumerate(products):
    product_link = product['link']
    print(f"Scraping category for: {product['name']} ({product_link})")

    category = scrape_category(product_link)
    product['category'] = category

    # Save the updated item_names back to the JSON file after each product
    with open('products_with_categories.json', 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=4)

    print(f"Updated {index + 1}/{len(products)}: {product['name']} -> {product['category']}")

    # Pause between requests to avoid overwhelming the server
    time.sleep(1)

print("Scraping completed. Data saved to 'products_with_categories.json'.")
