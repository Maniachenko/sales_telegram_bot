import requests
from bs4 import BeautifulSoup
import json

# Base URL and page suffix for iterating through pages
base_url = "https://www.akcniceny.cz/zbozi/albert+lekarna-alphega+barvy-a-laky+bene-napoje+lekarna-benu+billa+bonveno+cba+dr-max+filson-store+flop+flop-top+globus+idea-nabytek+intersport+jysk+kasvo+kaufland+kosik-cz+lidl+mobelix+mojelekarna+penny-market+pepco+pharmapoint+rabbit-reznictvi+ratio+rohlik-cz+rossmann+sconto-nabytek+tamda-foods+terno+tesco+tescoma+teta-drogerie+travel-free-s-r-o+trefa+vesna+xxxlutz+zeman-maso-uzeniny/"
page_suffix = "strana-{}"  # Suffix to append for pagination

# Number of pages to scrape
max_pages = 695


def scrape_page(url):
    """
    Scrape a single page for product names and links.

    :param url: The URL of the page to scrape.
    :return: A list of dictionaries with product names and links.
    """
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Select all product elements
    products = []
    product_elements = soup.select('div > div > div > h2 > a')

    for product_element in product_elements:
        name = product_element.get('title')
        link = product_element.get('href')
        if name and link:
            full_link = "https://www.akcniceny.cz" + link
            products.append({"name": name, "link": full_link})

    return products


def scrape_all_pages(base_url, max_pages):
    """
    Scrape all pages from the base URL and iterate through the number of pages.

    :param base_url: The base URL to start scraping from.
    :param max_pages: The maximum number of pages to scrape.
    :return: A list of all scraped products across all pages.
    """
    all_products = []
    for page in range(1, max_pages + 1):
        url = base_url if page == 1 else f"{base_url}{page_suffix.format(page)}"
        print(f"Scraping page {page}: {url}")

        # Scrape products from the current page
        products = scrape_page(url)
        all_products.extend(products)

    return all_products


# Start scraping and save results to a JSON file
if __name__ == "__main__":
    all_products = scrape_all_pages(base_url, max_pages)

    # Save the collected products to a JSON file
    with open('akcniceny_items.json', 'w', encoding='utf-8') as f:
        json.dump(all_products, f, ensure_ascii=False, indent=4)

    print(f"Scraping completed. {len(all_products)} products saved to 'akcniceny_items.json'.")
