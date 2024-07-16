import requests
import time
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# Initialize the Selenium WebDriver (Chrome in this case)
def initialize_driver():
    service = Service('/usr/bin/chromedriver')  # Update the path to your ChromeDriver
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run in headless mode for less overhead
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def fetch_html_selenium(url, driver):
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, 'body')))

        # Remove any overflow hidden styles by executing JavaScript
        driver.execute_script("""
            var elements = document.querySelectorAll('[style*="overflow: hidden"]');
            for (var i = 0; i < elements.length; i++) {
                elements[i].style.overflow = 'visible';
            }
        """)

        # Give time for the hidden elements to become visible
        time.sleep(2)

        return driver.page_source
    except Exception as e:
        print(f"Error fetching {url} with Selenium: {e}")
        return ""


def find_pdf_links(html, base_url):
    soup = BeautifulSoup(html, 'html.parser')
    a_tags = soup.find_all('a', href=True)
    pdf_links = [urljoin(base_url, a['href']) for a in a_tags if a['href'].lower().endswith('.pdf')]
    return pdf_links


def extract_domain(url):
    parsed_url = urlparse(url)
    return parsed_url.netloc


def interact_and_find_pdfs(driver, url):
    try:
        pdf_links = []

        # For Albert URL, click the specific divs
        if "albert.cz" in url:
            clickable_elements = driver.find_elements(By.CSS_SELECTOR, 'div[data-testid="leaflet-root"]')
        else:
            clickable_elements = None  # No specific clickable elements for other URLs for now

        if clickable_elements:
            for element in clickable_elements:
                try:
                    element.click()
                    time.sleep(2)  # Wait for any popups to appear

                    # Check for PDF links in the current page
                    html = driver.page_source
                    pdf_links.extend(find_pdf_links(html, driver.current_url))

                    # Handle any iframe popups
                    iframes = driver.find_elements(By.TAG_NAME, 'iframe')
                    for iframe in iframes:
                        driver.switch_to.frame(iframe)
                        time.sleep(1)
                        html = driver.page_source
                        pdf_links.extend(find_pdf_links(html, driver.current_url))
                        driver.switch_to.default_content()  # Switch back to the main content

                    # Close any potential popups if needed (you may need to customize this)
                    try:
                        alert = driver.switch_to.alert
                        alert.dismiss()
                    except:
                        pass

                except Exception as e:
                    print(f"Could not interact with element: {e}")
                    continue

        return pdf_links
    except Exception as e:
        # print(f"Error interacting with elements: {e}")
        return []


def main(urls):
    driver = initialize_driver()
    try:
        for url in urls:
            html = fetch_html_selenium(url, driver)
            pdf_links = find_pdf_links(html, url)
            domain = extract_domain(url)

            # Interact with elements to find additional PDF links
            more_pdf_links = interact_and_find_pdfs(driver, url)
            pdf_links.extend(more_pdf_links)

            if pdf_links:
                print(f"{domain}: {pdf_links}")
            else:
                print(f"{domain}: No PDF links found.")
    finally:
        driver.quit()


# List of URLs to process
urls = [
    "https://www.albert.cz/aktualni-letaky",
    "https://www.cba.cz/letaky/",
    "https://www.flop-potraviny.cz/akcni-letaky/",
    "https://prodejny.kaufland.cz/letak.html",
    "https://www.makro.cz/aktualni-nabidka",
    "http://ratio.cz/akce/",
    "https://itesco.cz/akcni-nabidky/letaky-a-katalogy/",
    "https://www.benenapoje.cz/",
    "https://www.esomarket.cz/",
    "https://www.globus.cz/",
    "https://tamdafoods.eu/cs/promotions",
    "https://www.prodejnyzeman.cz/akcni-nabidka/78",
    "https://www.billa.cz/akcni-letaky",
    "https://www.flop-potraviny.cz/akcni-letaky/",
    "https://www.lidl.cz/c/akcni-letak/s10008644",
    "https://www.penny.cz/nabidky/letaky",
    "https://www.travel-free.cz/akcni-nabidka"
]

if __name__ == "__main__":
    main(urls)
