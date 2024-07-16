import requests
from bs4 import BeautifulSoup
from PIL import Image
import io

def extract_store_name_and_id_from_url(url):
    parts = url.split('/')
    store_name_parts = parts[3].split('-')
    store_name = '_'.join(store_name_parts)
    last_id = url.rstrip('-').split('-')[-1]
    return store_name, last_id

def download_and_convert_first_image(base_url, max_pages):
    store_name, last_id = extract_store_name_and_id_from_url(base_url)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }

    from urllib.parse import urljoin
    base_scheme_domain = '/'.join(base_url.split('/')[:3])

    for page_num in range(max_pages):
        page_url = base_url + str(page_num)
        print(f"Processing {page_url}...")

        response = requests.get(page_url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            img_tags = soup.find_all('img')

            for img_tag in img_tags:
                if 'src' in img_tag.attrs:
                    img_url = urljoin(base_scheme_domain, img_tag['src'])

                    # Skip SVG files
                    if img_url.endswith('.svg'):
                        continue

                    img_response = requests.get(img_url, headers=headers)
                    if img_response.status_code == 200:
                        try:
                            img = Image.open(io.BytesIO(img_response.content))
                            if img.format:
                                if img.format != 'JPEG':
                                    img = img.convert("RGB")
                                file_name = f"{store_name}_{last_id}_page_{page_num}_image.jpeg"
                                img.save("./images/" + file_name)
                                print(f"Saved {file_name}")
                                break
                            else:
                                print(f"Downloaded content from {img_url} is not a recognized image format.")
                        except IOError:
                            print(f"Cannot identify image file from {img_url}. It might not be an image or is in an unsupported format.")
                    else:
                        print(f"Failed to download image from {img_url}")
                if img_tag == img_tags[-1]:
                    print("No suitable image found on the page.")
        else:
            print(f"Failed to fetch {page_url}")

base_url = "https://kompasslev.cz/tesco-letaky/aktualni-letak-na-tento-tyden-178469-"
max_pages = 27
download_and_convert_first_image(base_url, max_pages)
