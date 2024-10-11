import json

# Mapping for Czech to English character translation
czech_to_english_map = str.maketrans(
    "áčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ",
    "acdeeinorstuuyzACDEEINORSTUUYZ"
)


def preprocess_name(name):
    """
    Preprocess the given item name by:
    - Converting to lowercase
    - Translating Czech characters to their English equivalents
    - Removing tabs and newlines
    - Stripping leading/trailing spaces

    :param name: The original item name (string)
    :return: The preprocessed item name (string)
    """
    return name.lower().translate(czech_to_english_map).replace('\t', ' ').replace('\n', ' ').strip()


# List of JSON files to process
json_files = [
    "akcniceny_items.json",
    "albert_items.json",
    "billa_items.json",
    "globus_items.json",
    "penny_items.json",
    "tesco_items.json"
]

# Set to store unique item names after preprocessing
unique_items = set()

# Process each JSON file
for file_name in json_files:
    try:
        with open(file_name, 'r', encoding='utf-8') as file:
            data = json.load(file)

            # Ensure the data is a list before processing
            if isinstance(data, list):
                for item in data:
                    name = item.get('name', '')  # Get 'name' field or empty string if missing
                    if isinstance(name, str) and name:  # Only process valid non-empty strings
                        processed_name = preprocess_name(name)
                        unique_items.add(processed_name)

    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error processing {file_name}: {e}")

# Save all unique, preprocessed item names into a text file
with open('unique_item_names.txt', 'w', encoding='utf-8') as output_file:
    for item in sorted(unique_items):
        output_file.write(f"{item}\n")

print("Unique item names saved to 'unique_item_names.txt'.")
