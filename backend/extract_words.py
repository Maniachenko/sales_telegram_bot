import requests
from bs4 import BeautifulSoup
import re
from itertools import chain

def extract_number_of_pages(soup):
    pink_number_tag = soup.find('span', class_='pink-number')
    if not pink_number_tag:
        return 1
    sibling_text = pink_number_tag.next_sibling
    if sibling_text:
        numbers = re.findall(r'\d+', sibling_text)
        return int(numbers[-1]) if numbers else 1
    else:
        return 1

def generate_ngrams(words_list, n):
    return zip(*[words_list[i:] for i in range(n)])

def extract_words_from_url(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    texts = soup.stripped_strings
    words_set = set()
    bigrams_set = set()
    trigrams_set = set()

    for text in texts:
        # Split by space only for words
        words = text.lower().split()
        words_set.update(words)

        # Generate and add bigrams and trigrams
        bigrams = generate_ngrams(words, 2)
        trigrams = generate_ngrams(words, 3)

        bigrams_set.update([' '.join(bigram) for bigram in bigrams])
        trigrams_set.update([' '.join(trigram) for trigram in trigrams])

    return words_set, bigrams_set, trigrams_set

def iterate_pages_and_extract_words(base_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }

    response = requests.get(base_url, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    page_count = extract_number_of_pages(soup)

    all_words_set = set()
    all_bigrams_set = set()
    all_trigrams_set = set()

    base_url_parts = base_url.rsplit('-', 1)
    url_without_page_number = base_url_parts[0]

    for page_number in range(page_count):
        current_page_url = f"{url_without_page_number}-{page_number}"
        page_response = requests.get(current_page_url, headers=headers)
        page_response.raise_for_status()

        page_soup = BeautifulSoup(page_response.text, 'html.parser')
        texts = page_soup.stripped_strings

        words_set, bigrams_set, trigrams_set = extract_words_from_url(current_page_url)

        all_words_set.update(words_set)
        all_bigrams_set.update(bigrams_set)
        all_trigrams_set.update(trigrams_set)

    return all_words_set, all_bigrams_set, all_trigrams_set

urls = ["https://kompasslev.cz/billa-letaky/aktualni-letak-na-tento-tyden-181049-0",
        "https://kompasslev.cz/billa-letaky/aktualni-letak-na-tento-tyden-181367-0",
        "https://kompasslev.cz/billa-letaky/aktualni-letak-na-tento-tyden-181292-0",
        "https://kompasslev.cz/billa-letaky/aktualni-letak-na-tento-tyden-181289-0",
        "https://kompasslev.cz/billa-letaky/aktualni-letak-na-tento-tyden-181046-0",
        "https://kompasslev.cz/billa-letaky/aktualni-letak-na-tento-tyden-180863-0",
        "https://kompasslev.cz/billa-letaky/aktualni-letak-na-tento-tyden-180812-0",
        "https://kompasslev.cz/billa-letaky/aktualni-letak-na-tento-tyden-180665-0",
        "https://kompasslev.cz/globus-letaky/aktualni-letak-na-tento-tyden-181196-0",
        "https://kompasslev.cz/globus-letaky/aktualni-letak-na-tento-tyden-181247-0",
        "https://kompasslev.cz/globus-letaky/aktualni-letak-na-tento-tyden-181193-0",
        "https://kompasslev.cz/globus-letaky/aktualni-letak-na-tento-tyden-180314-0",
        "https://kompasslev.cz/globus-letaky/aktualni-letak-na-tento-tyden-180311-0",
        "https://kompasslev.cz/kaufland-letaky/aktualni-letak-na-tento-tyden-181459-0",
        "https://kompasslev.cz/kaufland-letaky/aktualni-letak-na-tento-tyden-180896-0",
        "https://kompasslev.cz/kaufland-letaky/aktualni-letak-na-tento-tyden-180800-0",
        "https://kompasslev.cz/kaufland-letaky/aktualni-letak-na-tento-tyden-180530-0",
        "https://kompasslev.cz/tesco-letaky/aktualni-letak-na-tento-tyden-181055-0",
        "https://kompasslev.cz/tesco-supermarket-letaky/aktualni-letak-na-tento-tyden-181052-0",
        "https://kompasslev.cz/tesco-supermarket-letaky/aktualni-letak-na-tento-tyden-180581-0",
        "https://kompasslev.cz/tesco-letaky/aktualni-letak-na-tento-tyden-180578-0",
        "https://kompasslev.cz/penny-market-letaky/aktualni-letak-na-tento-tyden-181157-0",
        "https://kompasslev.cz/penny-market-letaky/aktualni-letak-na-tento-tyden-180515-0",
        "https://kompasslev.cz/penny-market-letaky/aktualni-letak-na-tento-tyden-180272-0",
        "https://kompasslev.cz/penny-market-letaky/aktualni-letak-na-tento-tyden-179969-0",
        "https://kompasslev.cz/lidl-letaky/aktualni-letak-na-tento-tyden-181370-0",
        "https://kompasslev.cz/lidl-letaky/aktualni-letak-na-tento-tyden-180830-0",
        "https://kompasslev.cz/lidl-letaky/aktualni-letak-na-tento-tyden-181373-0",
        "https://kompasslev.cz/lidl-letaky/aktualni-letak-na-tento-tyden-181379-0",
        "https://kompasslev.cz/lidl-letaky/aktualni-letak-na-tento-tyden-181376-0",
        "https://kompasslev.cz/lidl-letaky/aktualni-letak-na-tento-tyden-180833-0"
        ]
all_words_from_all_urls, all_bigrams_from_all_urls, all_trigrams_from_all_urls = set(), set(), set()

for url in urls:
    words_set, bigrams_set, trigrams_set = iterate_pages_and_extract_words(url)
    all_words_from_all_urls.update(words_set)
    all_bigrams_from_all_urls.update(bigrams_set)
    all_trigrams_from_all_urls.update(trigrams_set)
    print(url, "finished")

# Saving the words, bigrams, and trigrams to a file
with open('data/collected_ngrams.txt', 'w') as file:
    for item in chain(sorted(all_words_from_all_urls), sorted(all_bigrams_from_all_urls), sorted(all_trigrams_from_all_urls)):
        file.write(f"{item}\n")

print(f"All words, bigrams, and trigrams from all URLs have been saved to collected_ngrams.txt.")
