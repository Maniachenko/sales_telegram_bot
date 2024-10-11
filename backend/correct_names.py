import json
import re
import hunspell
import itertools

# Czech to English character mapping
czech_to_english_map = str.maketrans(
    "áčçďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ",
    "accdeeinorstuuyzACDEEINORSTUUYZ"
)

def preprocess_text(text):
    """
    Preprocess text by removing unnecessary characters, converting to lowercase,
    and applying Czech to English conversion.

    :param text: The input text to preprocess.
    :return: The preprocessed text.
    """
    text = text.replace('\t', '').replace('\n', '').replace('\u00A0', ' ').replace("|", "").strip()
    text = text.lower().translate(czech_to_english_map)
    text = re.sub(r'[^\x00-\x7F]', ' ', text)  # Replace non-ASCII characters with spaces
    return text

# Initialize Hunspell with the Czech dictionary
hunspell_checker = hunspell.HunSpell('/usr/share/hunspell/cs_CZ.dic', '/usr/share/hunspell/cs_CZ.aff')

def generate_1li_combinations(word):
    """
    Generate all possible variants of a word by replacing 'i', 'l', '1' and other similar characters.

    :param word: The input word for which variants will be generated.
    :return: A list of generated word variants.
    """
    substitutions = {
        'i': ['i', 'l', '1'], 'l': ['i', 'l', '1'], '1': ['i', 'l', '1'],
        'r': ['r', 'j'], 'j': ['r', 'j'], 'e': ['e', 'o'], 'o': ['e', 'o']
    }
    positions = [i for i, char in enumerate(word) if char in substitutions]

    if not positions:
        return [word]

    variants = []
    for variant in itertools.product(*[substitutions[word[pos]] for pos in positions]):
        modified_word = list(word)
        for idx, pos in enumerate(positions):
            modified_word[pos] = variant[idx]
        variants.append(''.join(modified_word))

    return variants

class TrieNode:
    """Represents a node in a Trie (prefix tree) data structure."""
    def __init__(self):
        self.children = {}
        self.is_word = False

class Trie:
    """Trie (prefix tree) data structure for storing words and performing word searches."""
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word):
        """
        Insert a word and its variants into the Trie.

        :param word: The word to insert into the Trie.
        """
        variants = generate_1li_combinations(word)
        for variant in variants:
            node = self.root
            for char in variant:
                if char not in node.children:
                    node.children[char] = TrieNode()
                node = node.children[char]
            node.is_word = True

    def search(self, word):
        """
        Search for a word in the Trie.

        :param word: The word to search for in the Trie.
        :return: True if the word is found, False otherwise.
        """
        node = self.root
        for char in word:
            if char not in node.children:
                return False
            node = node.children[char]
        return node.is_word

    def find_all_words(self, text):
        """
        Finds all valid word candidates using the Trie for the given text.

        :param text: The input text to search within.
        :return: A list of tuples (word, start, end) where start and end are the indices in the text.
        """
        words = []
        for start in range(len(text)):
            node = self.root
            for end in range(start, len(text)):
                char = text[end]
                if char not in node.children:
                    break
                node = node.children[char]
                if node.is_word:
                    words.append((text[start:end + 1], start, end + 1))
        return words

def calculate_penalty(word):
    """
    Penalize small words to avoid splitting into meaningless segments.

    :param word: The word for which the penalty is calculated.
    :return: The penalty score for the word.
    """
    return len(word) if len(word) > 3 else -10

def best_word_combination(words, text_length):
    """
    Dynamic programming function to find the best way to split a sentence into words.

    :param words: A list of valid word candidates (word, start, end).
    :param text_length: The length of the input text.
    :return: The best split of words as a list.
    """
    dp = [(-float('inf'), [])] * (text_length + 1)
    dp[0] = (0, [])  # Base case

    for word, start, end in words:
        score = calculate_penalty(word)
        if dp[start][0] + score > dp[end][0]:
            dp[end] = (dp[start][0] + score, dp[start][1] + [word])

    return dp[text_length][1]

def process_items_with_trie_and_hunspell(detected_items, trie):
    """
    Process detected items by splitting concatenated words using the Trie and Hunspell.

    :param detected_items: A list of detected items containing OCR text.
    :param trie: An instance of the Trie used for word search.
    :return: A list of corrected items with processed names.
    """
    corrected_items = []

    for item in detected_items:
        for obj in item['detected_objects']:
            if obj['class_id'] == 0:
                original_text = obj['got_ocr_text']
                concatenated_text = "".join(preprocess_text(original_text).split())

                # Find all possible valid words using the Trie
                found_words = trie.find_all_words(concatenated_text)

                # Find the best word combination using dynamic programming
                best_split = best_word_combination(found_words, len(concatenated_text))

                # Use Hunspell for words not found in the Trie
                final_processed_words = []
                for word in best_split:
                    if not trie.search(word):
                        if hunspell_checker.spell(word):
                            final_processed_words.append(word)
                        else:
                            suggestions = hunspell_checker.suggest(word)
                            final_processed_words.append(suggestions[0] if suggestions else word)
                    else:
                        final_processed_words.append(word)

                obj['processed_name'] = " ".join(final_processed_words)
                print(f"Original: {original_text} -> Processed: {obj['processed_name']}")

        corrected_items.append(item)

    return corrected_items

# Load detected_items.json file
with open('detected_items.json', 'r', encoding='utf-8') as f:
    detected_items = json.load(f)

# Load unique item names from the file and preprocess them
with open('./item_names/unique_item_names.txt', 'r', encoding='utf-8') as f:
    item_names = f.readlines()
    words = [preprocess_text(line).split() for line in item_names]
    flat_words = [word for sublist in words for word in sublist]

# Build the Trie with preprocessed words
trie = Trie()
for word in flat_words:
    trie.insert(word)

# Process the detected items using the Trie and Hunspell
corrected_items = process_items_with_trie_and_hunspell(detected_items, trie)

# Save the corrected detected items to a new file
with open('corrected_detected_items.json', 'w', encoding='utf-8') as f:
    json.dump(corrected_items, f, ensure_ascii=False, indent=4)

print("Processing completed. Data saved to 'corrected_detected_items.json'.")
