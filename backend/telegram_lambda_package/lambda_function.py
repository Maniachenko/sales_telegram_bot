import ast
import copy
import tempfile
import requests
import json
import os
import re
import boto3
from boto3.dynamodb.conditions import Attr
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

# Constants for the S3 bucket and Telegram API
BUCKET_NAME = os.environ.get('BUCKET_NAME')
TOKEN = os.environ.get('TOKEN')
API_URL = f"https://api.telegram.org/bot{TOKEN}"

# Initialize DynamoDB resources
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

# DynamoDB table references
user_preferences_table = dynamodb.Table('user_preferences')
pdf_metadata_table = dynamodb.Table('pdf_metadata')
detected_data_table = dynamodb.Table("detected_data")


# --------------- AWS Handling ---------------
def download_file_from_s3(filename_path, local_path):
    """
    Downloads a file from the specified S3 bucket to a local file path.

    :param filename_path: The path of the file in the S3 bucket.
    :param local_path: The local path where the file should be saved.

    :raises ValueError: If the provided filename_path is not a valid string.
    """
    # Ensure the S3 file path is a valid string before proceeding with the download
    if not isinstance(filename_path, str) or not filename_path:
        raise ValueError(f"Invalid S3 filename path: {filename_path}")

    # Log the download operation for debugging purposes
    logger.debug(f"Downloading file from S3 bucket: {filename_path} to local path: {local_path}")

    # Perform the file download from the specified S3 bucket to the local path
    s3.download_file(BUCKET_NAME, filename_path, local_path)


# --------------- User Preferences Handling ---------------

def get_user_preferences(chat_id):
    """
    Retrieves user preferences from DynamoDB for the given chat_id.
    If no preferences are found, it returns a default preference with 'new_user' state.
    """
    response = user_preferences_table.get_item(Key={'chat_id': str(chat_id)})
    return response.get('Item', {"state": "new_user"})


def save_user_preferences(chat_id, preferences):
    """
    Saves or updates user preferences in DynamoDB for the given chat_id.
    """
    user_preferences_table.put_item(Item={
        'chat_id': str(chat_id),
        **preferences
    })


def get_user_language(chat_id):
    """
    Retrieves the language preference of the user from DynamoDB.
    """
    preferences = get_user_preferences(chat_id)
    return preferences.get('language', None)


def set_user_language(chat_id, language_code):
    """
    Sets the language preference for the user and saves it in DynamoDB.
    """
    preferences = get_user_preferences(chat_id)
    preferences['language'] = language_code
    save_user_preferences(chat_id, preferences)


def save_user_state(chat_id, state):
    """
    Saves the user's current interaction state in DynamoDB, allowing for persistence of state across interactions.

    :param chat_id: The chat ID of the user.
    :param state: The interaction state (e.g., menu state, ongoing search, etc.) to be saved.
    """
    preferences = get_user_preferences(chat_id)  # Retrieve the current preferences for the user
    preferences['state'] = state  # Set the new state for the user
    save_user_preferences(chat_id, preferences)  # Save the updated preferences (including the state) to DynamoDB


def get_user_state(chat_id):
    """
    Retrieves the user's current interaction state from DynamoDB.

    :param chat_id: The chat ID of the user.
    :return: The current state of the user, or None if no state is set.
    """
    preferences = get_user_preferences(chat_id)  # Fetch the user preferences from DynamoDB
    return preferences.get('state', None)  # Return the current state, or None if no state is set


# --------------- Shop Selection History Handling ---------------

def save_user_selected_shops_history(chat_id, shops):
    """
    Saves the user's selected shop history in DynamoDB.
    Ensures the history only contains the 10 most recent entries.
    """
    preferences = get_user_preferences(chat_id)
    history = preferences.setdefault('selected_shops_history', [])

    if shops not in history:
        history.append(copy.deepcopy(shops))
        if len(history) > 10:  # Keep history to last 10 items
            history.pop(0)

    preferences['selected_shops_history'] = history
    save_user_preferences(chat_id, preferences)


def get_user_selected_shops_history(chat_id):
    """
    Retrieves the user's selected shops history from DynamoDB.
    """
    preferences = get_user_preferences(chat_id)
    return preferences.get('selected_shops_history', [])


# --------------- Tracked Items Handling ---------------


def get_tracked_items(chat_id):
    """
    Retrieves the list of items the user is tracking.
    """
    preferences = get_user_preferences(chat_id)
    return preferences.get('tracked_items', [])


def add_tracked_item(chat_id, item_name):
    """
    Adds an item to the user's tracking list, if it's not already being tracked.
    Returns True if the item is newly added, False if it already exists.
    """
    preferences = get_user_preferences(chat_id)
    tracked_items = preferences.setdefault('tracked_items', [])

    if item_name not in tracked_items:
        tracked_items.append(item_name)
        save_user_preferences(chat_id, preferences)
        return True
    return False


def remove_tracked_item(chat_id, item_name):
    """
    Removes an item from the user's tracking list.
    """
    preferences = get_user_preferences(chat_id)
    tracked_items = preferences.get('tracked_items', [])

    if item_name in tracked_items:
        tracked_items.remove(item_name)
        save_user_preferences(chat_id, preferences)


# --------------- Shop Inclusion and Exclusion Handling ---------------

def exclude_all_shops(chat_id):
    """
    Excludes all shops by retrieving all shop names from the pdf_metadata table
    and storing them in the user's preferences.
    """
    unique_shops = set()
    exclusive_start_key = None

    while True:
        scan_kwargs = {'ProjectionExpression': 'shop_name'}
        if exclusive_start_key:
            scan_kwargs['ExclusiveStartKey'] = exclusive_start_key

        response = pdf_metadata_table.scan(**scan_kwargs)

        for item in response.get('Items', []):
            unique_shops.add(item['shop_name'])

        exclusive_start_key = response.get('LastEvaluatedKey')
        if not exclusive_start_key:
            break

    preferences = get_user_preferences(chat_id)
    preferences['excluded_shops'] = list(unique_shops)
    save_user_preferences(chat_id, preferences)

    return preferences


def get_excluded_shops(chat_id):
    """
    Retrieves the list of excluded shops from the user's preferences.
    """
    preferences = get_user_preferences(chat_id)
    return set(preferences.get('excluded_shops', []))


def get_included_shops(chat_id):
    """
    Returns the list of shops that are included for tracking by comparing all shops
    to the excluded shops in the user's preferences.
    """
    excluded_shops = get_excluded_shops(chat_id)
    response = pdf_metadata_table.scan(ProjectionExpression="shop_name")
    all_shops = set(item['shop_name'] for item in response['Items'])
    included_shops = all_shops - excluded_shops
    return sorted(included_shops) if included_shops else []


def exclude_shop(chat_id, shop_name):
    """
    Adds a shop to the user's excluded shops list.
    """
    preferences = get_user_preferences(chat_id)
    excluded_shops = get_excluded_shops(chat_id)

    if shop_name not in excluded_shops:
        excluded_shops.add(shop_name)
        preferences['excluded_shops'] = list(excluded_shops)
        save_user_preferences(chat_id, preferences)


def include_shop(chat_id, shop_name):
    """
    Removes a shop from the user's excluded shops list, thereby including it in tracking.
    """
    preferences = get_user_preferences(chat_id)
    excluded_shops = get_excluded_shops(chat_id)

    if shop_name in excluded_shops:
        excluded_shops.remove(shop_name)
        preferences['excluded_shops'] = list(excluded_shops)
        save_user_preferences(chat_id, preferences)


# --------------- General Shop Management ---------------

def get_all_shops():
    """
    Retrieves a list of all unique shop names from the pdf_metadata table.
    """
    response = pdf_metadata_table.scan(ProjectionExpression="shop_name")
    unique_shops = set(item['shop_name'] for item in response['Items'])
    return sorted(unique_shops)


# --------------- Sale Sheet and Media Preferences Handling ---------------

def is_sale_sheet_enabled(chat_id):
    """
    Returns whether the sale sheet is enabled for the user.
    """
    preferences = get_user_preferences(chat_id)
    return preferences.get('sale_sheet_enabled', True)


def toggle_sale_sheet(chat_id):
    """
    Toggles the sale sheet preference for the user and returns the updated state.
    """
    preferences = get_user_preferences(chat_id)
    current = preferences.get('sale_sheet_enabled', True)
    preferences['sale_sheet_enabled'] = not current
    save_user_preferences(chat_id, preferences)
    return not current


def is_photo_group_enabled(chat_id):
    """
    Returns whether photo groups are enabled for the user.
    """
    preferences = get_user_preferences(chat_id)
    return preferences.get('photo_group_enabled', True)  # Default is True


def set_photo_group_enabled(chat_id, enabled):
    """
    Enables or disables photo groups for the user.
    """
    preferences = get_user_preferences(chat_id)
    preferences['photo_group_enabled'] = enabled
    save_user_preferences(chat_id, preferences)


def is_text_info_enabled(chat_id):
    """
    Returns whether text info is enabled for the user.
    """
    preferences = get_user_preferences(chat_id)
    return preferences.get('text_info_enabled', False)  # Default is False


def set_text_info_enabled(chat_id, enabled):
    """
    Enables or disables text info for the user.
    """
    preferences = get_user_preferences(chat_id)
    preferences['text_info_enabled'] = enabled
    save_user_preferences(chat_id, preferences)


# --------------- Search Handling ---------------

czech_to_english_map = str.maketrans(
    "áčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ",
    "acdeeinorstuuyzACDEEINORSTUUYZ"
)


def find_item(item_name, shop_name=None, included_shops=None):
    """
    Searches for an item in the detected_data_table based on the given item_name,
    optional shop_name, and list of included_shops. It uses n-gram matching for flexible name search.

    :param item_name: The name of the item to search for.
    :param shop_name: (Optional) The specific shop to search in.
    :param included_shops: (Optional) A list of shops to limit the search.
    :return: A list of matching items with their prices and other metadata.
    """
    results = []

    # Preprocess the input item name: lowercase and convert Czech characters to English equivalents
    item_name_lower = item_name.lower().translate(czech_to_english_map).replace('\n', ' ').replace('\t', ' ').strip()

    # Generate n-grams from the user's input (for flexible matching)
    query_ngrams = generate_ngrams(item_name_lower, 2)

    # Define the DynamoDB scan query to filter for valid items
    scan_kwargs = {
        'FilterExpression': Attr('valid').eq(True)  # Only include valid items
    }

    # Apply additional filters for shop_name or included_shops if provided
    if shop_name:
        scan_kwargs['FilterExpression'] &= Attr('shop_name').eq(shop_name)
    if included_shops:
        scan_kwargs['FilterExpression'] &= Attr('shop_name').is_in(included_shops)

    # Perform the scan operation on DynamoDB
    response = detected_data_table.scan(**scan_kwargs)

    # Iterate over each returned item from the scan
    for item in response.get('Items', []):
        item_shop_name = item.get('shop_name', 'Unknown Shop')

        # Preprocess both original and processed item names
        processed_item_name = item.get('processed_item_name', '').lower().translate(czech_to_english_map).strip()
        db_item_name = item.get('item_name', '').lower().translate(czech_to_english_map).strip()

        # Concatenate both names and generate n-grams from the result
        concatenated_name = f"{db_item_name}".strip()
        item_ngrams = generate_ngrams(concatenated_name, 2)

        # Count the intersection between user query n-grams and item name n-grams
        ngram_intersection_count = len(query_ngrams.intersection(item_ngrams))

        # If there's a sufficient match, add the item to the result
        if ngram_intersection_count >= len(query_ngrams)-1:
            price = find_price_for_item(item)
            results.append({
                'item_name': item.get('item_name', ''),
                'price': price,
                'shop_name': item_shop_name,
                'ngram_score': ngram_intersection_count,
                'image_name': item.get('image_id')  # Include the image filename if available
            })

    # Sort results by n-gram score in descending order
    results = sorted(results, key=lambda x: x['ngram_score'], reverse=True)

    return results


def find_price_for_item(obj):
    """
    Extracts different price types (item_price, item_initial_price, item_member_price)
    from a DynamoDB item and returns them as a formatted string.

    :param obj: The DynamoDB item containing price information.
    :return: A formatted string containing price information or "Price not found" if no prices exist.
    """
    prices = []

    def try_convert_to_dict(value):
        """
        Utility function to safely convert a string into a dictionary if possible.

        :param value: The value to attempt conversion.
        :return: A dictionary if successful, otherwise the original value.
        """
        if isinstance(value, str):
            try:
                return ast.literal_eval(value)  # Attempt to evaluate as a Python literal
            except (ValueError, SyntaxError):
                try:
                    return json.loads(value)  # Attempt to parse as JSON
                except (ValueError, TypeError):
                    return value  # Return original value if conversion fails
        return value

    # Try to convert price fields to dictionaries, if applicable
    processed_price = try_convert_to_dict(obj.get('processed_item_price', None))
    initial_price = try_convert_to_dict(obj.get('processed_item_initial_price', None))
    member_price = try_convert_to_dict(obj.get('processed_item_member_price', None))

    # Handle processed_item_price
    if isinstance(processed_price, dict):
        prices.append(f"Price: {processed_price.get('item_price')}\n")
    elif processed_price:  # If it's a string or number
        prices.append(f"Price: {processed_price}\n")

    # Handle processed_item_initial_price
    if isinstance(initial_price, dict):
        prices.append(f"Initial price: {initial_price.get('item_initial_price')}\n")
    elif initial_price:
        prices.append(f"Initial price: {initial_price}\n")

    # Handle processed_item_member_price
    if isinstance(member_price, dict):
        prices.append(f"Member price: {member_price.get('item_member_price')}\n")
    elif member_price:
        prices.append(f"Member price: {member_price}\n")

    # Return the price strings or "Price not found" if no prices are available
    return "".join(prices) if prices else "Price not found"


def generate_ngrams(text, n):
    """
    Generates n-grams from a given text.

    :param text: The input text from which n-grams are generated.
    :param n: The number of characters per n-gram.
    :return: A set of n-grams.
    """
    words = re.split(r'\W+', text)  # Split text by any non-alphanumeric characters
    ngrams = set()

    # Generate n-grams for each word in the text
    for word in words:
        for i in range(len(word) - n + 1):
            ngrams.add(word[i:i + n])

    return ngrams


# --------------- User Interaction Handling ---------------

def get_available_languages():
    """
    Returns a dictionary of supported languages and their respective codes.
    """
    return {
        'en': 'English',
        'ru': 'Русский',
        'uk': 'Українська',
        'cs': 'Čeština'
    }


# Language selection prompt
def language_selection(chat_id):
    """
    Sends a language selection prompt to the user with inline buttons for language choices.

    :param chat_id: The Telegram chat ID of the user.
    """
    url = f"{API_URL}/sendMessage"
    buttons = {
        "inline_keyboard": [
            [{"text": "English", "callback_data": "lang_en"}],
            [{"text": "Русский", "callback_data": "lang_ru"}],
            [{"text": "Українська", "callback_data": "lang_uk"}],
            [{"text": "Čeština", "callback_data": "lang_cs"}],
        ]
    }
    payload = {
        "chat_id": chat_id,
        "text": "Welcome! Please select your language:",
        "reply_markup": buttons
    }
    requests.post(url, json=payload)


# Main menu display
def main_menu(chat_id):
    """
    Displays the main menu to the user with various options for tracking and comparing shop items.

    :param chat_id: The Telegram chat ID of the user.
    """
    url = f"{API_URL}/sendMessage"
    buttons = {
        "keyboard": [
            [{"text": "🔍 Search for item"}],
            [{"text": "🛒 Add shop item to track price"}],
            [{"text": "🛍 Compare shopping list over shops"}],
            [{"text": "⚙️ Settings"}],
            [{"text": "ℹ️ About project"}],
        ],
        "resize_keyboard": True
    }
    payload = {
        "chat_id": chat_id,
        "text": "Main Menu",
        "reply_markup": buttons
    }
    requests.post(url, json=payload)


# Including shop to track at the start
def include_user_tracking_shops(chat_id):
    """
    Sends a list of shops for the user to start tracking items in. If no shops are excluded,
    it loads all shops into the excluded list first.

    :param chat_id: The Telegram chat ID of the user.
    """
    shops = list(get_excluded_shops(chat_id))

    # If no excluded shops, exclude all shops initially
    if shops == []:
        exclude_all_shops(chat_id)

    # Send the list of shops with options to select from
    requests.post(f"{API_URL}/sendMessage", json={
        "chat_id": chat_id,
        "text": "Please select a shop from the list for item search and tracking. You can change this later in 'Settings'.",
        "reply_markup": {
            "keyboard": [[shop] for shop in get_excluded_shops(chat_id)] + [["⬅️ Back to main menu"]],
            "resize_keyboard": True
        }
    })

    # Save the user's state as selecting shops
    save_user_state(chat_id, '/start_selecting_shops')


# Settings menu display with dynamic labels for photo group and text info
def settings_menu(chat_id):
    """
    Displays the settings menu with dynamic labels for photo group and text info toggling options.

    :param chat_id: The Telegram chat ID of the user.
    """
    url = f"{API_URL}/sendMessage"

    # Get the current state of photo groups and text info to display in the button labels
    photo_group_state = "Enabled" if is_photo_group_enabled(chat_id) else "Disabled"
    text_info_state = "Enabled" if is_text_info_enabled(chat_id) else "Disabled"

    # Create buttons with dynamic labels based on current settings
    buttons = {
        "keyboard": [
            [{"text": "🚫 Exclude some shops from tracking"}],
            [{"text": "✅ Include some shops in tracking"}],
            [{"text": "🛑 Remove shop item from tracking price"}],
            [{"text": "📄 Turn on/off sale sheet PDF"}],
            [{"text": f"📄 Turn {'off' if photo_group_state == 'Enabled' else 'on'} items photo groups"}],
            [{"text": f"📄 Turn {'off' if text_info_state == 'Enabled' else 'on'} items text info"}],
            [{"text": "🌐 Change interface language"}],
            [{"text": "⬅️ Back to main menu"}],
        ],
        "resize_keyboard": True
    }

    # Send the settings menu
    payload = {
        "chat_id": chat_id,
        "text": "Select an option from Settings:",
        "reply_markup": buttons
    }
    requests.post(url, json=payload)


# Sending images as an album
def send_images_as_album(chat_id, media_group, shop_name):
    """
    Sends a group of images (as an album) to the user via Telegram.

    :param chat_id: The Telegram chat ID of the user.
    :param media_group: A list of tuples (S3 image path, local temp path) representing images to send.
    :param shop_name: The name of the shop to include in the caption of the first image.
    """
    media = []
    files = {}

    # Loop through the media group and process each image
    for i, (s3_image_path, temp_path) in enumerate(media_group):
        try:
            # Extract the image filename from the S3 path
            image_name = os.path.basename(s3_image_path)

            # Log the S3 path and temporary file for debugging
            logger.debug(f"Downloading image from S3: {s3_image_path} to {temp_path}")

            # Use a temporary file to handle the downloaded image
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file_path = temp_file.name
                # Download the image from S3 into the temporary file
                download_file_from_s3(s3_image_path, temp_file_path)

                # Read the file content for use in the Telegram API
                with open(temp_file_path, 'rb') as image_file:
                    image_content = image_file.read()

                # Prepare the files dictionary (it must have unique keys for each image)
                files[f"photo{i}"] = (image_name, image_content)

                # Prepare the media array with references to the attached photos
                media.append({
                    "type": "photo",
                    "media": f"attach://photo{i}",
                    "caption": shop_name if i == 0 else ""  # Add shop name as caption only to the first image
                })

                # Remove the temporary file after reading
                os.remove(temp_file_path)

        except Exception as e:
            logger.error(f"Error processing image {image_name}: {str(e)}")

    # If no valid media is available, log an error and return
    if not media:
        logger.error("No valid media to send.")
        return

    # Send the media group using the Telegram API
    try:
        response = requests.post(f"{API_URL}/sendMediaGroup", files=files, data={
            "chat_id": chat_id,
            "media": json.dumps(media)  # Convert the media list to a JSON string
        })

        logger.debug(f"Telegram API response for sendMediaGroup: {response.status_code}, {response.text}")
    except Exception as e:
        logger.error(f"Error sending media group: {str(e)}")


# Process messages and button responses
def process_message(update):
    chat_id = update['message']['chat']['id']
    text = update['message'].get('text')

    # Ensure user preferences are loaded
    state = get_user_state(chat_id)

    # Handle /start command
    if text == "/start":
        description = "Welcome to the Smart Shopping Bot! I will help you track prices, manage sale sheets, and find the best shopping paths."
        requests.post(f"{API_URL}/sendMessage", json={"chat_id": chat_id, "text": description})

        if state == "new_user":
            # Set default preferences for new users
            preferences = get_user_preferences(chat_id)
            if 'photo_group_enabled' not in preferences:
                preferences['photo_group_enabled'] = True  # Default to show photo groups
            if 'text_info_enabled' not in preferences:
                preferences['text_info_enabled'] = False  # Default to hide text info
            save_user_preferences(chat_id, preferences)

            # Guide user through initial steps of setup: language selection or shop inclusion
            if get_user_language(chat_id) is None:
                language_selection(chat_id)
                save_user_state(chat_id, None)
            elif get_included_shops(chat_id) is None:
                include_user_tracking_shops(chat_id)
                save_user_state(chat_id, None)
            else:
                main_menu(chat_id)
                save_user_state(chat_id, None)
        else:
            # If user is not new, take them directly to the main menu
            main_menu(chat_id)
            save_user_state(chat_id, None)

    # Handling the shop selection state
    elif state == '/start_selecting_shops':
        if text == "➕ Add another shop":
            include_user_tracking_shops(chat_id)
        elif text == "➡️ Save tracking shop list. Return to the main menu":
            if not get_included_shops(chat_id):
                # No shops have been included yet, notify the user
                requests.post(f"{API_URL}/sendMessage", json={
                    "chat_id": chat_id,
                    "text": "Please select at least one shop from the list:",
                    "reply_markup": {
                        "keyboard": [[shop] for shop in sorted(get_excluded_shops(chat_id))] + [
                            ["⬅️ Back to main menu"]],
                        "resize_keyboard": True}
                })
            else:
                # At least one shop is included, allow returning to the menu
                main_menu(chat_id)
                save_user_state(chat_id, None)
        else:
            # Get the list of excluded shops
            shops = list(get_excluded_shops(chat_id))
            # Check if the input text is a valid shop
            if text in shops:
                include_shop(chat_id, text)
                # Ask if the user wants to add more shops or return to the main menu
                requests.post(f"{API_URL}/sendMessage", json={
                    "chat_id": chat_id,
                    "text": "Do you want to add more shops or continue with the selected shop list?",
                    "reply_markup": {
                        "keyboard": [["➕ Add another shop"], ["➡️ Save tracking shop list. Return to the main menu"]],
                        "resize_keyboard": True
                    }
                })
                save_user_state(chat_id, '/start_selecting_shops')
            elif text == "⬅️ Back to main menu":
                # Check if any shops are included before allowing return to the main menu
                if not get_included_shops(chat_id):
                    requests.post(f"{API_URL}/sendMessage", json={
                        "chat_id": chat_id,
                        "text": "Please select at least one shop before returning to the menu:",
                        "reply_markup": {"keyboard": [[shop] for shop in shops] + [["⬅️ Back to main menu"]],
                                         "resize_keyboard": True}
                    })
                else:
                    main_menu(chat_id)
                    save_user_state(chat_id, None)

            else:
                # The user input is not a valid shop, ask them to select again
                requests.post(f"{API_URL}/sendMessage", json={
                    "chat_id": chat_id,
                    "text": "Please select a valid shop from the list:",
                    "reply_markup": {"keyboard": [[shop] for shop in shops] + [["⬅️ Back to main menu"]],
                                     "resize_keyboard": True}
                })

    # Handle search functionality
    elif text == "🔍 Search for item":
        requests.post(f"{API_URL}/sendMessage", json={
            "chat_id": chat_id,
            "text": "Please enter the name of the item you want to search for.",
            "reply_markup": {"keyboard": [["⬅️ Back to main menu"]], "resize_keyboard": True}
        })
        save_user_state(chat_id, 'searching_item')


    # Handle main menu options
    elif text == "🛒 Add shop item to track price":
        requests.post(f"{API_URL}/sendMessage", json={
            "chat_id": chat_id,
            "text": "Please provide the name of the shop item you want to track.",
            "reply_markup": {"keyboard": [["⬅️ Back to main menu"]], "resize_keyboard": True}
        })
        save_user_state(chat_id, 'adding_item')

    elif text == "⚙️ Settings":
        settings_menu(chat_id)
        save_user_state(chat_id, 'in_settings')

    elif text == "🛍 Compare shopping list over shops":
        # Clean preferences after unexpected last user manipulations
        preferences = get_user_preferences(chat_id)
        preferences['selected_shops'] = []
        preferences['item_list'] = []
        save_user_preferences(chat_id, preferences)

        requests.post(f"{API_URL}/sendMessage", json={
            "chat_id": chat_id,
            "text": "Please select a shop or list of shops from your history.",
            "reply_markup": {
                "keyboard": [["List of all shops"], ["Lists of shops from history"], ["⬅️ Back to main menu"]],
                "resize_keyboard": True}
        })
        save_user_state(chat_id, 'selecting_shops')

    elif text == "ℹ️ About project":
        about_text = "This bot helps you optimize your shopping by tracking prices, managing sale sheets, and finding the best shopping routes."
        requests.post(f"{API_URL}/sendMessage", json={"chat_id": chat_id, "text": about_text})
        main_menu(chat_id)
        save_user_state(chat_id, None)

    # Handle states
    else:
        if state == 'adding_item' or state == "searching_item":
            if text == "⬅️ Back to main menu":
                main_menu(chat_id)
                save_user_state(chat_id, None)
            else:
                item_name = text.strip()

                found_items = find_item(item_name, included_shops=get_included_shops(chat_id))

                if state == 'adding_item':
                    # Save the item for tracking and notify the user
                    added = add_tracked_item(chat_id, item_name)

                    if added:
                        response = f"'{item_name}' saved for tracking. I will notify you when '{item_name}' has a valid sale."
                        requests.post(f"{API_URL}/sendMessage", json={"chat_id": chat_id, "text": response})
                    else:
                        tracked_items = get_tracked_items(chat_id)
                        response = f"'{item_name}' is already in your tracking list. Here is your current list:\n" + "\n".join(
                            tracked_items)
                        requests.post(f"{API_URL}/sendMessage", json={"chat_id": chat_id, "text": response})
                        main_menu(chat_id)
                        save_user_state(chat_id, None)
                        return

                if found_items:
                    items_by_shop = {}
                    for found_item in found_items:
                        shop_name = found_item['shop_name']

                        if shop_name not in items_by_shop:
                            items_by_shop[shop_name] = []
                        items_by_shop[shop_name].append(found_item)

                    photo_group_enabled = is_photo_group_enabled(chat_id)
                    text_info_enabled = is_text_info_enabled(chat_id)

                    for shop_name, shop_items in items_by_shop.items():
                        response = f"Here is what I found for '{item_name}' in {shop_name}:\n"
                        media_group = []

                        for found_item in shop_items:
                            if text_info_enabled:
                                response += f"- {found_item['item_name']} at {shop_name}: {found_item['price']}\n"

                            s3_image_dir = found_item.get('image_name')
                            # Collecting images for the media group (album) if photo group is enabled
                            if photo_group_enabled and s3_image_dir:
                                # Extract the filename from the full S3 path
                                image_filename = os.path.basename(s3_image_dir)
                                local_image_path = f"/tmp/{image_filename}"

                                # Instead of reading the file content, pass the file path directly
                                media_group.append((s3_image_dir, local_image_path))
                                logger.debug(f"Image added to media_group: {local_image_path}")

                        if media_group and photo_group_enabled:
                            logger.debug(f"Sending media group for {shop_name} with {len(media_group)} images")
                            send_images_as_album(chat_id, media_group, shop_name)

                        if text_info_enabled:
                            requests.post(f"{API_URL}/sendMessage", json={"chat_id": chat_id, "text": response})
                else:
                    requests.post(f"{API_URL}/sendMessage",
                                  json={"chat_id": chat_id, "text": f"No items found for '{item_name}'."})
                main_menu(chat_id)
                save_user_state(chat_id, None)

        elif state == 'in_settings':
            if text == "⬅️ Back to main menu":
                main_menu(chat_id)
                save_user_state(chat_id, None)
            elif text == "📄 Turn on items photo groups" or text == "📄 Turn off items photo groups":
                # Toggle the photo group setting
                current_photo_group_state = is_photo_group_enabled(chat_id)
                current_text_info_state = is_text_info_enabled(chat_id)

                # Check if both features would be disabled
                if not current_text_info_state and current_photo_group_state:
                    # Cannot disable photo groups if text info is already disabled
                    requests.post(f"{API_URL}/sendMessage", json={
                        "chat_id": chat_id,
                        "text": "At least one of the options (photo groups or text info) must be enabled. Text info is already disabled, so photo groups cannot be turned off."
                    })
                else:
                    # Safe to toggle photo groups
                    set_photo_group_enabled(chat_id, not current_photo_group_state)
                    new_state = "enabled" if not current_photo_group_state else "disabled"
                    requests.post(f"{API_URL}/sendMessage", json={
                        "chat_id": chat_id,
                        "text": f"Item photo groups are now {new_state}."
                    })
                    settings_menu(chat_id)

            elif text == "📄 Turn on items text info" or text == "📄 Turn off items text info":
                # Toggle the text info setting
                current_photo_group_state = is_photo_group_enabled(chat_id)
                current_text_info_state = is_text_info_enabled(chat_id)

                # Check if both features would be disabled
                if not current_photo_group_state and current_text_info_state:
                    # Cannot disable text info if photo groups are already disabled
                    requests.post(f"{API_URL}/sendMessage", json={
                        "chat_id": chat_id,
                        "text": "At least one of the options (photo groups or text info) must be enabled. Photo groups are already disabled, so text info cannot be turned off."
                    })
                else:
                    # Safe to toggle text info
                    set_text_info_enabled(chat_id, not current_text_info_state)
                    new_state = "enabled" if not current_text_info_state else "disabled"
                    requests.post(f"{API_URL}/sendMessage", json={
                        "chat_id": chat_id,
                        "text": f"Item text info is now {new_state}."
                    })
                    settings_menu(chat_id)
            elif text == "🚫 Exclude some shops from tracking":
                # Retrieve the included shops that can be excluded
                included_shops = get_included_shops(chat_id)

                # If there are no included shops, inform the user
                if not included_shops:
                    requests.post(f"{API_URL}/sendMessage", json={
                        "chat_id": chat_id,
                        "text": "No shops are currently included for tracking."
                    })
                else:
                    # Present the user with a list of shops that can be excluded
                    requests.post(f"{API_URL}/sendMessage", json={
                        "chat_id": chat_id,
                        "text": "Please select a shop to exclude from tracking:",
                        "reply_markup": {
                            "keyboard": [[shop] for shop in included_shops] + [["⬅️ Back to settings"]],
                            "resize_keyboard": True}
                    })
                    save_user_state(chat_id, 'excluding_shop')
            elif text == "✅ Include some shops in tracking":
                # Retrieve the excluded shops that can be included
                excluded_shops = get_excluded_shops(chat_id)

                # If all shops are already included, inform the user
                if not excluded_shops:
                    requests.post(f"{API_URL}/sendMessage", json={
                        "chat_id": chat_id,
                        "text": "All shops are currently included for tracking."
                    })
                else:
                    # Present the user with a list of excluded shops that can be included
                    requests.post(f"{API_URL}/sendMessage", json={
                        "chat_id": chat_id,
                        "text": "Please select a shop to include in tracking:",
                        "reply_markup": {
                            "keyboard": [[shop] for shop in sorted(excluded_shops)] + [["⬅️ Back to settings"]],
                            "resize_keyboard": True}
                    })
                    save_user_state(chat_id, 'including_shop')
            elif text == "🛑 Remove shop item from tracking price":
                items_to_remove = get_tracked_items(chat_id)
                if items_to_remove:
                    requests.post(f"{API_URL}/sendMessage", json={
                        "chat_id": chat_id,
                        "text": "Select an item to remove from tracking:",
                        "reply_markup": {"keyboard": [[item] for item in items_to_remove] + [["⬅️ Back to settings"]],
                                         "resize_keyboard": True}
                    })
                    save_user_state(chat_id, 'removing_item')
                else:
                    requests.post(f"{API_URL}/sendMessage", json={
                        "chat_id": chat_id,
                        "text": "You don't have any items being tracked.",
                    })
                    settings_menu(chat_id)
                    save_user_state(chat_id, 'in_settings')

        elif state == 'excluding_shop':
            if text == "⬅️ Back to settings":
                settings_menu(chat_id)
                save_user_state(chat_id, 'in_settings')
            else:
                exclude_shop(chat_id, text)
                requests.post(f"{API_URL}/sendMessage",
                              json={"chat_id": chat_id, "text": f"Shop '{text}' excluded from tracking."})
                settings_menu(chat_id)
                save_user_state(chat_id, 'in_settings')

        elif state == 'including_shop':
            if text == "⬅️ Back to settings":
                settings_menu(chat_id)
                save_user_state(chat_id, 'in_settings')
            else:
                include_shop(chat_id, text)
                requests.post(f"{API_URL}/sendMessage",
                              json={"chat_id": chat_id, "text": f"Shop '{text}' included for tracking."})
                settings_menu(chat_id)
                save_user_state(chat_id, 'in_settings')

        elif state == 'removing_item':
            if text == "⬅️ Back to settings":
                settings_menu(chat_id)
                save_user_state(chat_id, 'in_settings')
            else:
                remove_tracked_item(chat_id, text)
                requests.post(f"{API_URL}/sendMessage",
                              json={"chat_id": chat_id, "text": f"Item '{text}' removed from tracking."})
                settings_menu(chat_id)
                save_user_state(chat_id, 'in_settings')

        elif state == "shop_list_history":
            if text == "⬅️ Back to main menu":
                main_menu(chat_id)
                save_user_state(chat_id, None)
            else:
                try:
                    index = int(text) - 1
                    shop_history = get_user_selected_shops_history(chat_id)
                    if 0 <= index < len(shop_history):
                        selected_history_list = shop_history[index]
                        preferences = get_user_preferences(chat_id)
                        preferences['selected_shops'] = selected_history_list
                        save_user_preferences(chat_id, preferences)
                        # Proceed to item entry
                        requests.post(f"{API_URL}/sendMessage", json={
                            "chat_id": chat_id,
                            "text": "Please provide your shopping list, one per line and send.",
                            "reply_markup": {"keyboard": [["⬅️ Back to main menu"]], "resize_keyboard": True}
                        })
                        preferences['item_list'] = []
                        save_user_preferences(chat_id, preferences)
                        save_user_state(chat_id, 'entering_items')
                    else:
                        raise IndexError
                except (ValueError, IndexError):
                    # Handle invalid input
                    shop_history = get_user_selected_shops_history(chat_id)
                    keyboard_buttons = [[str(i + 1)] for i in range(len(shop_history))] + [["⬅️ Back to main menu"]]
                    text_message = "Invalid selection. Please choose a number from the list:\n"
                    for i, shop_list in enumerate(shop_history):
                        text_message += f"{i + 1}. {', '.join(shop_list)}\n"
                    requests.post(f"{API_URL}/sendMessage", json={
                        "chat_id": chat_id,
                        "text": text_message,
                        "reply_markup": {"keyboard": keyboard_buttons, "resize_keyboard": True}
                    })

        elif state == 'selecting_shops':
            if text == "⬅️ Back to main menu":
                main_menu(chat_id)
                save_user_state(chat_id, None)
            elif text == "➡️ Continue with shop list":
                preferences = get_user_preferences(chat_id)
                selected_shops = preferences.get('selected_shops', [])
                if not selected_shops:
                    # No shops selected yet
                    shops = get_all_shops()
                    requests.post(f"{API_URL}/sendMessage", json={
                        "chat_id": chat_id,
                        "text": "You have not selected any shops. Please select at least one shop.",
                        "reply_markup": {"keyboard": [[shop] for shop in shops] + [["⬅️ Back to main menu"]],
                                         "resize_keyboard": True}
                    })
                    save_user_state(chat_id, 'selecting_shops')
                else:
                    logger.debug(selected_shops)
                    save_user_selected_shops_history(chat_id, selected_shops)
                    # Proceed to item entry
                    requests.post(f"{API_URL}/sendMessage", json={
                        "chat_id": chat_id,
                        "text": "Please provide your shopping list, one by line and send.",
                        "reply_markup": {"keyboard": [["⬅️ Back to main menu"]], "resize_keyboard": True}
                    })

                    # Not to overwrite history
                    preferences = get_user_preferences(chat_id)
                    preferences['item_list'] = []
                    save_user_preferences(chat_id, preferences)
                    save_user_state(chat_id, 'entering_items')
            elif text == "Lists of shops from history":
                # Get the user's shop history
                shop_history = get_user_selected_shops_history(chat_id)
                if shop_history:
                    # Build the keyboard buttons with numbers
                    keyboard_buttons = [[str(i + 1)] for i in range(len(shop_history))] + [["⬅️ Back to main menu"]]

                    # Corrected prompt and display
                    text_message = "Please select a shop list from your history:\n"
                    for i, shop_list in enumerate(shop_history):
                        text_message += f"{i + 1}. {', '.join(shop_list)}\n"

                    # Send the message with the keyboard
                    requests.post(f"{API_URL}/sendMessage", json={
                        "chat_id": chat_id,
                        "text": text_message,
                        "reply_markup": {"keyboard": keyboard_buttons, "resize_keyboard": True}
                    })

                    # Save the user state
                    save_user_state(chat_id, 'shop_list_history')
                else:
                    shops = get_all_shops()
                    # The user input is not a valid shop
                    requests.post(f"{API_URL}/sendMessage", json={
                        "chat_id": chat_id,
                        "text": "You don't have any history saved list. Please select a shop from the list:",
                        "reply_markup": {"keyboard": [[shop] for shop in shops] + [["⬅️ Back to main menu"]],
                                         "resize_keyboard": True}
                    })
            else:
                # Get the list of available shops
                shops = get_all_shops()
                # Check if the input text is a valid shop
                if text in shops:
                    # Save the selected shop
                    preferences = get_user_preferences(chat_id)
                    selected_shops = preferences.get('selected_shops', [])
                    if text not in selected_shops:
                        selected_shops.append(text)
                        preferences['selected_shops'] = selected_shops
                        save_user_preferences(chat_id, preferences)
                    # Ask if the user wants to add more shops or continue
                    requests.post(f"{API_URL}/sendMessage", json={
                        "chat_id": chat_id,
                        "text": "Do you want to add more shops or continue with the selected shop list?",
                        "reply_markup": {
                            "keyboard": [["➕ Add another shop"], ["➡️ Continue with shop list"],
                                         ["⬅️ Back to main menu"]],
                            "resize_keyboard": True
                        }
                    })
                    save_user_state(chat_id, 'confirming_shops')

                else:
                    # The user input is not a valid shop
                    requests.post(f"{API_URL}/sendMessage", json={
                        "chat_id": chat_id,
                        "text": "Please select a shop from the list:",
                        "reply_markup": {"keyboard": [[shop] for shop in shops] + [["⬅️ Back to main menu"]],
                                         "resize_keyboard": True}
                    })


        elif state == 'confirming_shops':
            if text == "⬅️ Back to main menu":
                main_menu(chat_id)
                save_user_state(chat_id, None)
            elif text == "➕ Add another shop":
                # Exclude already selected shops
                preferences = get_user_preferences(chat_id)
                selected_shops = preferences.get('selected_shops', [])
                shops = [shop for shop in get_all_shops() if shop not in selected_shops]
                if shops:
                    requests.post(f"{API_URL}/sendMessage", json={
                        "chat_id": chat_id,
                        "text": "Please select shop from the list:",
                        "reply_markup": {"keyboard": [[shop] for shop in shops] + [
                            ["⬅️ Back to main menu"] + ["➡️ Continue with shop list"]],
                                         "resize_keyboard": True}
                    })
                    save_user_state(chat_id, 'selecting_shops')
                else:
                    # All shops have been selected
                    requests.post(f"{API_URL}/sendMessage", json={
                        "chat_id": chat_id,
                        "text": "You have selected all available shops.",
                        "reply_markup": {
                            "keyboard": [["➡️ Continue with shop list"], ["⬅️ Back to main menu"]],
                            "resize_keyboard": True
                        }
                    })
                    save_user_state(chat_id, 'confirming_shops')

            elif text == "➡️ Continue with shop list":
                preferences = get_user_preferences(chat_id)
                selected_shops = preferences.get('selected_shops', [])
                if not selected_shops:
                    # No shops selected yet
                    shops = get_all_shops()
                    requests.post(f"{API_URL}/sendMessage", json={
                        "chat_id": chat_id,
                        "text": "You have not selected any shops. Please select at least one shop.",
                        "reply_markup": {"keyboard": [[shop] for shop in shops] + [["⬅️ Back to main menu"]],
                                         "resize_keyboard": True}
                    })
                    save_user_state(chat_id, 'selecting_shops')
                else:
                    logger.debug(selected_shops)
                    save_user_selected_shops_history(chat_id, selected_shops)
                    # Proceed to item entry
                    requests.post(f"{API_URL}/sendMessage", json={
                        "chat_id": chat_id,
                        "text": "Please provide your shopping list, one by line and send.",
                        "reply_markup": {"keyboard": [["⬅️ Back to main menu"]], "resize_keyboard": True}
                    })

                    # Not to overwrite history
                    preferences = get_user_preferences(chat_id)
                    preferences['item_list'] = []
                    save_user_preferences(chat_id, preferences)
                    save_user_state(chat_id, 'entering_items')

            else:
                # Handle unexpected input
                requests.post(f"{API_URL}/sendMessage", json={
                    "chat_id": chat_id,
                    "text": "Please select an option from the menu."
                })

        elif state == 'entering_items':
            if text == "⬅️ Back to main menu":
                main_menu(chat_id)
                save_user_state(chat_id, None)
            else:
                # Add item to the list
                preferences = get_user_preferences(chat_id)
                item_list = preferences.get('item_list', [])
                item_list.extend(text.split('\n'))
                preferences['item_list'] = item_list
                save_user_preferences(chat_id, preferences)
                preferences = get_user_preferences(chat_id)
                selected_shops = preferences.get('selected_shops', [])
                item_list = preferences.get('item_list', [])
                response = "Here are the items found in the selected shops:\n"
                # Retrieve user preferences for photo group and text info settings
                photo_group_enabled = is_photo_group_enabled(chat_id)
                text_info_enabled = is_text_info_enabled(chat_id)
                # List to collect all images for the media group
                for shop in selected_shops:
                    if text_info_enabled:
                        response += f"\nItems in {shop}:\n"
                    media_group = []  # List to collect all images for the media group
                    # Loop through each item in the item list and search for it in the specified shop
                    for item_name in item_list:
                        found_items = find_item(item_name, shop)

                        if found_items:
                            for found_item in found_items:
                                # Extract price and image path details from the found item
                                price = found_item.get('price')
                                s3_image_dir = found_item.get('image_name')

                                logger.debug(f"Found item: {found_item}")
                                logger.debug(f"Price: {price}, Image Path: {s3_image_dir}")

                                # Include price details in the response if text info is enabled
                                if text_info_enabled:
                                    # Add the item price or "Price not found" based on availability
                                    if price:
                                        response += f"- {found_item['item_name']} at {shop}: {price}\n"
                                    else:
                                        response += f"- {found_item['item_name']} at {shop}: Price not found\n"

                                # Process the image only if the photo group is enabled
                                if photo_group_enabled and s3_image_dir:
                                    # Extract the filename from the full S3 path
                                    image_filename = os.path.basename(s3_image_dir)
                                    local_image_path = f"/tmp/{image_filename}"

                                    # Add the image filename and its corresponding local path to the media group
                                    media_group.append((s3_image_dir, local_image_path))
                                    logger.debug(f"Image added to media_group: {local_image_path}")
                        else:
                            # If the item is not found in the shop, add a not found message to the response
                            response += f"- {item_name}: Not found in {shop}\n"

                    # After looping through items, send the images as an album if there are any and photo group is enabled
                    logger.debug(f"Media group length: {len(media_group)}. Photo group enabled: {photo_group_enabled}")
                    if media_group and photo_group_enabled:
                        logger.debug(f"Sending media group for shop: {shop}")
                        send_images_as_album(chat_id, media_group, shop)
                        media_group.clear()  # Clear the media group after sending to avoid duplicate entries
                    else:
                        logger.debug(f"No images to send or photo group is disabled")

                # Send the final response with text results if text info is enabled
                if text_info_enabled:
                    requests.post(f"{API_URL}/sendMessage", json={"chat_id": chat_id, "text": response})

                main_menu(chat_id)
                save_user_state(chat_id, None)

                # Clear selected shops and item list
                preferences['selected_shops'] = []
                preferences['item_list'] = []
                save_user_preferences(chat_id, preferences)

        else:
            if text == "⬅️ Back to main menu":
                main_menu(chat_id)
                save_user_state(chat_id, None)
            else:
                requests.post(f"{API_URL}/sendMessage", json={"chat_id": chat_id,
                                                              "text": "I'm sorry, I didn't understand that. Please choose an option from the menu."})


# Handle callback queries from inline buttons (e.g., language selection)
def process_callback_query(update):
    """
    Processes the callback queries triggered by inline buttons, such as language selection.
    :param update: The update payload containing the callback query details.
    """
    query = update['callback_query']
    chat_id = query['message']['chat']['id']  # Extract the chat ID of the user
    message_id = query['message']['message_id']  # Extract the message ID to edit it later
    data = query.get('data')  # Retrieve the callback data (e.g., 'lang_en')
    callback_query_id = query['id']  # The ID for answering the callback query

    # Check if the callback is related to language selection (data starts with 'lang_')
    if data.startswith('lang_'):
        language_code = data.split('_')[1]  # Extract the language code (e.g., 'en', 'ru')
        set_user_language(chat_id, language_code)  # Save the selected language to user preferences

        # Answer the callback query to stop Telegram's "loading" animation
        answer_payload = {
            "callback_query_id": callback_query_id,
            "text": "Language updated!",  # Confirmation message to the user
            "show_alert": False  # Do not show a popup, just stop the loading animation
        }
        requests.post(f"{API_URL}/answerCallbackQuery", json=answer_payload)

        # Edit the original message to remove the inline keyboard and update the text
        new_text = f"Language selected! You have set your language to: {get_available_languages().get(language_code, 'Unknown')}"
        edit_payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": new_text,
            "reply_markup": {}  # Remove the inline keyboard by setting an empty reply_markup
        }
        requests.post(f"{API_URL}/editMessageText", json=edit_payload)

        # Proceed to include the shops tracking list for the user
        include_user_tracking_shops(chat_id)


def lambda_handler(event, context):
    """
    This function will act as the webhook to handle Telegram updates when deployed to AWS Lambda.
    It will process both regular messages and callback queries.
    """
    try:
        # Parse the body from the incoming event
        if 'body' in event:
            update = json.loads(event['body'])  # Extract the JSON body from the Lambda event

            # Process message or callback query based on the update type
            if 'message' in update:
                process_message(update)  # Call your process_message function
            elif 'callback_query' in update:
                process_callback_query(update)  # Call your process_callback_query function

            # Return a success response to Telegram
            return {
                'statusCode': 200,
                'body': json.dumps({'status': 'ok'})
            }
        else:
            logger.error('No body found in the request')
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Bad Request'})
            }

    except Exception as e:
        logger.error(f"Error processing the request: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal Server Error'})
        }
