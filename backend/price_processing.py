import json
from output_prices_analyze import (
    process_esomarket, process_penny, process_billa, process_albert_hypermarket,
    process_tesco_supermarket, process_lidl, process_kaufland, process_flop_top,
    process_travel_free, process_cba_potraviny, process_bene, process_cba_premium,
    process_lidl_shop, process_cba_market, process_makro, process_globus,
    process_tamda_foods, process_ratio
)

# Load JSON data from a file
def load_json(file_path):
    """
    Load JSON data from the specified file.

    :param file_path: Path to the JSON file.
    :return: Parsed JSON data.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

# Save JSON data to a file
def save_json(data, file_path):
    """
    Save JSON data to the specified file.

    :param data: Data to save.
    :param file_path: Path to the JSON file.
    """
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

# Process prices based on class_id and shop name
def process_price_by_class_id(shop_name, got_ocr_text, class_id):
    """
    Process price information based on the shop name and class ID.

    :param shop_name: Name of the shop.
    :param got_ocr_text: OCR extracted text.
    :param class_id: ID indicating the type of price (e.g., item price, member price).
    :return: Processed price or None if not applicable.
    """
    price_type_map = {
        2: "item_price",
        5: "item_member_price",
        7: "item_initial_price"
    }

    price_type = price_type_map.get(class_id)
    if not price_type:
        return None

    # Dispatch to appropriate processing function based on shop_name
    shop_processors = {
        "EsoMarket": process_esomarket,
        "Penny": lambda text: process_penny(text, price_type),
        "Billa": lambda text: process_billa(text, price_type),
        "Albert Hypermarket": lambda text: process_albert_hypermarket(text, price_type),
        "Albert Supermarket": lambda text: process_albert_hypermarket(text, price_type),
        "Tesco Supermarket": lambda text: process_tesco_supermarket(text, price_type),
        "Tesco Hypermarket": lambda text: process_tesco_supermarket(text, price_type),
        "Lidl": process_lidl,
        "Kaufland": lambda text: process_kaufland(text, price_type),
        "Flop Top": lambda text: process_flop_top(text, price_type),
        "Flop": lambda text: process_flop_top(text, price_type),
        "Travel Free": lambda text: process_travel_free(text, price_type),
        "CBA Potraviny": process_cba_potraviny,
        "Bene": process_bene,
        "CBA Premium": process_cba_premium,
        "Lidl Shop": process_lidl_shop,
        "CBA Market": process_cba_market,
        "Makro": lambda text: process_makro(text, price_type),
        "Globus": lambda text: process_globus(text, price_type),
        "Tamda Foods": lambda text: process_tamda_foods(text, price_type),
        "Ratio": process_ratio
    }

    processor = shop_processors.get(shop_name)
    return processor(got_ocr_text) if processor else None

# Process detected items and add price information
def process_detected_items(detected_items):
    """
    Process detected items to extract and assign price information.

    :param detected_items: List of detected items.
    :return: Updated list of detected items with processed price information.
    """
    for item in detected_items:
        shop_name = item.get("shop_name")
        for detected_object in item.get("detected_objects", []):
            got_ocr_text = detected_object.get("got_ocr_text")
            class_id = detected_object.get("class_id")

            # Process price based on shop name and class ID
            processed_price = process_price_by_class_id(shop_name, got_ocr_text, class_id)

            # If a valid price is processed, add it to the object
            if processed_price:
                detected_object["processed_price"] = processed_price

    return detected_items

# Main function
if __name__ == "__main__":
    input_file = "corrected_detected_items.json"
    output_file = "updated_detected_items.json"

    # Load, process, and save detected items
    detected_items = load_json(input_file)
    updated_items = process_detected_items(detected_items)
    save_json(updated_items, output_file)

    print(f"Processed and saved the updated items to {output_file}")