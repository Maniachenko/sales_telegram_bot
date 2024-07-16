import re

import requests
from pdf2image import convert_from_path
import cv2
import numpy as np
from pathlib import Path
import tempfile
from ultralytics import YOLO
import pytesseract
import easyocr
import matplotlib.pyplot as plt
import os
from fuzzywuzzy import process

reader = easyocr.Reader(['cs'])


#
# with open("data/collected_ngrams.txt", "r") as file:
#     lines = [line.strip() for line in file.readlines()]
#
# grams_1 = []
# grams_2 = []
# grams_3 = []
#
# # Iterate through each line and classify it based on the number of spaces
# for line in lines:
#     space_count = line.count(' ')
#
#     if space_count == 0:
#         grams_1.append(line)
#     elif space_count == 1:
#         grams_2.append(line)
#     elif space_count == 2:
#         grams_3.append(line)

def load_variations_from_file(filename):
    with open(filename, 'r') as file:
        return [line.strip() for line in file.readlines()]


# Load variations
price_per_unit_variations = load_variations_from_file('data/price_per_unit_variations.txt')
measure_variations = load_variations_from_file('data/measure_variations.txt')
percent_variations = load_variations_from_file('data/percent_variations.txt')
price_variations = load_variations_from_file('data/price_variations.txt')
collected_ngrams = load_variations_from_file('data/collected_ngrams.txt')


def download_pdf(url):
    response = requests.get(url)
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_file.write(response.content)  # Write the content of the response, not the URL
        return tmp_file.name


def pdf_to_images(pdf_path, dpi=300):
    for img in convert_from_path(pdf_path, dpi=dpi, first_page=None, last_page=None):
        yield np.array(img)


def preprocess_for_ocr_dynamic(img_fragment):
    gray_img = cv2.cvtColor(img_fragment, cv2.COLOR_BGR2GRAY)

    blurred_img = cv2.GaussianBlur(gray_img, (5, 5), 0)

    _, bin_img = cv2.threshold(blurred_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    contrast_img = clahe.apply(bin_img)

    return contrast_img


model = YOLO("item_detector/runs/detect/train/weights/best.pt")
item_model = YOLO("item_processing/runs/detect/train/weights/best.pt")


def save_image_with_incremental_name(base_path, image, base_name="processed_image", extension=".png"):
    counter = 0
    while True:
        if counter == 0:
            file_name = f"{base_name}{extension}"
        else:
            file_name = f"{base_name}{counter}{extension}"
        file_path = os.path.join(base_path, file_name)
        if not os.path.exists(file_path):
            plt.figure()
            plt.imshow(image)
            plt.title('Processed Image')
            plt.axis('off')
            plt.savefig(file_path, bbox_inches='tight')
            plt.close()
            print(f"Image saved as {file_name}")
            break
        counter += 1


def process_image_for_numbers(image, bounding_box):
    # Extract the subimage using bounding box coordinates
    x, y, w, h = bounding_box
    subimage = image[y:y + h, x:x + w]

    # Resize the image 3 times its original size
    subimage_resized = cv2.resize(subimage, (0, 0), fx=3, fy=3)

    # Convert to grayscale
    gray_image = cv2.cvtColor(subimage_resized, cv2.COLOR_BGR2GRAY)

    # Invert the grayscale image to handle different color contrasts
    inverted_gray_image = 255 - gray_image

    # Apply Gaussian blur
    blurred_image = cv2.GaussianBlur(inverted_gray_image, (5, 5), 0)

    # Adaptive thresholding to handle different lighting conditions
    thresh_image = cv2.adaptiveThreshold(blurred_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                         cv2.THRESH_BINARY, 11, 2)

    # Use morphological operations to emphasize areas likely to contain numbers
    # This can be adjusted based on the specific characteristics of your price tags
    kernel = np.ones((3, 3), np.uint8)
    morph_image = cv2.morphologyEx(thresh_image, cv2.MORPH_CLOSE, kernel)
    morph_image = cv2.dilate(morph_image, kernel, iterations=2)

    # Find contours - potentially useful for isolating numbers
    contours, _ = cv2.findContours(morph_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filter contours that might represent numbers (based on size, aspect ratio, etc.)
    number_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > 50]  # Example threshold

    # Draw contours on the image (for visualization)
    cv2.drawContours(subimage_resized, number_contours, -1, (0, 255, 0), 2)

    # Convert BGR to RGB for correct color representation
    rgb_image = cv2.cvtColor(subimage_resized, cv2.COLOR_BGR2RGB)

    # Optional: save or process the image further here

    return rgb_image, number_contours


def process_image(image, bounding_box):
    x, y, w, h = bounding_box
    subimage = image[y:y + h, x:x + w]

    subimage_resized = cv2.resize(subimage, (0, 0), fx=3, fy=3)

    gray_image = cv2.cvtColor(subimage_resized, cv2.COLOR_BGR2GRAY)

    inverted_gray_image = 255 - gray_image

    def process_grayscale_image(gray_image):
        blurred_image = cv2.GaussianBlur(gray_image, (5, 5), 0)

        _, thresh_image = cv2.threshold(blurred_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        kernel = np.ones((5, 5), np.uint8)
        dilated_image = cv2.dilate(thresh_image, kernel, iterations=1)

        contours, _ = cv2.findContours(dilated_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        rects = [cv2.boundingRect(contour) for contour in contours if cv2.contourArea(contour) > 100]
        rects.sort(key=lambda x: x[0])

        return dilated_image, rects

    dilated_image, rects = process_grayscale_image(gray_image)
    reverted_dilated_image, reverted_rects = process_grayscale_image(inverted_gray_image)

    for rect in rects + reverted_rects:
        cv2.rectangle(subimage_resized, (rect[0], rect[1]), (rect[0] + rect[2], rect[1] + rect[3]), (0, 255, 0), 2)

    rgb_image = cv2.cvtColor(subimage_resized, cv2.COLOR_BGR2RGB)

    return dilated_image, rects, reverted_dilated_image, reverted_rects


def correct_words(ocr_words, dictionary):
    corrected_words = []
    for word in ocr_words:
        closest_match, match_score = process.extractOne(word, dictionary)

        threshold_score = 80

        if match_score > threshold_score:
            corrected_words.append(closest_match)
        else:
            corrected_words.append(word)

    return corrected_words


def clean_price(text):
    # Handles price formats, ensuring spacing before 'Kč' and correct formatting
    text = re.sub(r'[^\d,\.Kč]', '', text)  # Remove unwanted characters
    text = re.sub(r'(\d)(Kč)', r'\1 Kč', text)  # Ensure space before 'Kč'
    match = re.search(r'\d{1,4}(?:[.,]\d{2})?\s?Kč', text)
    return match.group(0) if match else "Invalid price"


def clean_volume(text):
    # Corrects common OCR errors like 'l' mistaken for '1'
    text = text.replace('l', '1').replace('O', '0')
    match = re.search(r'\d{1,3}(?:[.,]\d{1,2})?\s?(l|g|kg|ml)', text)
    return match.group(0) if match else "Invalid volume"


def clean_price_per_unit(text):
    # Cleans and formats price per unit, ensuring correct use of space and currency
    text = re.sub(r'[^\d,\.=Kčg]', '', text)
    text = re.sub(r'(\d)g', r'\1 g', text)
    match = re.search(r'\d{1,3}(?:[.,]\d{2})?g=\d{1,4}(?:[.,]\d{2})?\s?Kč', text)
    return match.group(0) if match else "Invalid price per unit"


def clean_percentage(text):
    # Strips unnecessary characters and checks for a percentage format
    text = text.replace('~', '').replace(' ', '')
    match = re.search(r'\d{1,3}%', text)
    return match.group(0) if match else "Invalid percentage"


def clean_item_name(text):
    # Replaces common OCR misreads with correct terms
    replacements = {"1O0g": "100g", "Irole": "role", "1l": "1 l", "0d14": "od 14"}
    pattern = re.compile('|'.join(replacements.keys()))
    return pattern.sub(lambda x: replacements[x.group()], text.strip())


def clean_text_by_class(class_name, text):
    # Directs the text to the appropriate cleaning function based on the item's class
    cleaners = {
        "price_per_unit": clean_price_per_unit,
        "price": clean_price,
        "volume": clean_volume,
        "sale": clean_percentage,
        "prcnt": clean_percentage,
        "name": clean_item_name
    }
    return cleaners.get(class_name, lambda x: x)(text)


def levenshtein_distance(s1, s2):
    """ Compute the Levenshtein distance between two strings. """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def split_and_match(ocr_text, variations):
    if '=' in ocr_text:
        quantity_part, price_part = ocr_text.split('=', 1)
        # Filter variations to find those relevant to the parts split by '='
        quantity_variations = {var.split('=')[0]: var for var in variations if '=' in var}
        price_variations = {var.split('=')[1]: var for var in variations if '=' in var}

        # Find the nearest variations for both parts
        nearest_quantity = find_nearest_variation(quantity_part.strip(), list(quantity_variations.keys()))
        nearest_price = find_nearest_variation(price_part.strip(), list(price_variations.keys()))

        return f"{nearest_quantity}={nearest_price}"
    return ocr_text  # Return original text if no '=' is found


def classify_and_match(detected_texts, price_variations, price_per_unit_variations):
    parts = detected_texts.split()
    corrected_price = None
    corrected_price_per_unit = None

    # Filter parts to identify those with '=' considered as price per unit
    parts_with_equals = [part for part in parts if '=' in part]

    if parts_with_equals:
        # Handle parts that are identified as price per unit
        for part in parts_with_equals:
            corrected_price_per_unit = split_and_match(part, price_per_unit_variations)
    else:
        # Choose the longest part when no '=' is found, typically indicating a price or an important numeric detail
        if len(parts) > 1:
            longest_part = max(parts, key=len)
            corrected_price = find_nearest_variation_with_preference(longest_part, price_variations, prefer_length=True)
        elif parts:
            corrected_price = find_nearest_variation(parts[0], price_variations)

    return corrected_price, corrected_price_per_unit


def find_nearest_variation(ocr_part, part_variations):
    """ Find the closest variation to the OCR part using Levenshtein distance. """
    ocr_part = ocr_part.lower()
    nearest_variations = sorted(part_variations, key=lambda var: levenshtein_distance(var.lower(), ocr_part))[:1]
    return nearest_variations


def find_nearest_variation_with_preference(ocr_text, part_variations, prefer_length=False):
    ocr_text = ocr_text.lower()
    sorted_variations = sorted(part_variations, key=lambda var: levenshtein_distance(var.lower(), ocr_text))

    if prefer_length:
        preferred_matches = [var for var in sorted_variations if len(var) == len(ocr_text) + 1]
        if preferred_matches:
            return preferred_matches[0]

    return sorted_variations[0] if sorted_variations else None


def parse_volume_text(volume_text, measure_variations):
    # Split on 'x' to separate possible quantity from the measurement
    parts = volume_text.split('x')
    if len(parts) > 1:
        # Focus on the last part for measurement (after 'x')
        measurement_part = parts[-1].strip()
    else:
        measurement_part = parts[0].strip()

    # Find the nearest measurement variation for the measurement part
    return find_nearest_variation(measurement_part, measure_variations)


def detect_and_display(image_generator):
    for img_array in image_generator:
        img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        results = model(img_array)

        height, width, _ = img_array.shape

        for result in results:
            if result.boxes is not None:
                for box in result.boxes.xyxy:
                    x1, y1, x2, y2 = map(int, box.cpu().numpy().tolist()[:4])
                    x1, y1, x2, y2 = max(0, x1 - int((x2 - x1) * 0.07)), max(0, y1 - int((y2 - y1) * 0.07)), min(width,
                                                                                                                 x2 + int(
                                                                                                                     (
                                                                                                                             x2 - x1) * 0.07)), min(
                        height, y2 + int((y2 - y1) * 0.07))

                    img_fragment = img_array[y1:y2, x1:x2]
                    fragment_results = item_model(img_fragment)

                    for fragment_result in fragment_results:
                        if fragment_result.boxes is not None:
                            for i, box in enumerate(fragment_result.boxes.xyxy):
                                fx1, fy1, fx2, fy2 = map(int, box.cpu().numpy())
                                class_name = item_model.names[int(fragment_result.boxes.cls[i])]
                                sub_img_fragment = img_fragment[fy1:fy2, fx1:fx2]

                                ocr_result = reader.readtext(sub_img_fragment)
                                detected_texts = ' '.join([text for _, text, _ in ocr_result])

                                if class_name == "item_price_per_unit":
                                    nearest_variations = split_and_match(detected_texts, price_per_unit_variations)
                                elif class_name == 'item_price':
                                    nearest_variations = classify_and_match(detected_texts, price_variations,
                                                                            price_per_unit_variations)
                                elif class_name == "item_name":
                                    nearest_variations = find_nearest_variation(detected_texts, collected_ngrams)
                                elif class_name == "item_volume":
                                    nearest_variations = parse_volume_text(detected_texts, measure_variations)
                                elif class_name == "item_sale_prcnt":
                                    nearest_variations = find_nearest_variation(detected_texts, percent_variations)
                                else:
                                    nearest_variations = [detected_texts]  # No correction

                                print(
                                    f"Detected Class: {class_name}, OCR Text: {detected_texts}, Corrections: {nearest_variations}")
            else:
                print("No detections.")

    # Items Name (1 item name, 2 item names)
    # Measure unit volume (bedynka, 1ks; 1l, 200 g, 1 kg, roli, 0.5 l+zaloha, 1 Kus, 270 g a dalsi, cena za 1 kus pri koupu baleni 6 kus, cen za multipack)
    # price
    # sale percentage
    # sale type (pri koupi od ... ks; blla klub, 3 as 2)

    # nearest_1grams = find_nearest_ngrams(cleaned_text, grams_1)
    # nearest_2grams = find_nearest_ngrams(cleaned_text, grams_2)
    # nearest_3grams = find_nearest_ngrams(cleaned_text, grams_3)
    #
    # for word, ngrams in nearest_1grams.items():
    #     print(f"{word}: Nearest 1-grams: {ngrams}")
    # for word, ngrams in nearest_2grams.items():
    #     print(f"{word}: Nearest 2-grams: {ngrams}")
    # for word, ngrams in nearest_3grams.items():
    #     print(f"{word}: Nearest 3-grams: {ngrams}")
    # print("\n")


pdf_link = 'https://view.publitas.com/64069/1862306/pdfs/48909f10-f9ad-4442-ad5a-d7a5a0bdc033.pdf?response-content-disposition=attachment%3B+filename%2A%3DUTF-8%27%27BILLA.cz%2520-%2520Velk%25C3%25BD%2520let%25C3%25A1k%2520od%2520%25C3%25BAter%25C3%25BD%25202.%25204.%2520do%2520%25C3%25BAter%25C3%25BD%25209.%25204.%25202024.pdf'
pdf_path = download_pdf(pdf_link)
image_generator = pdf_to_images(pdf_path, dpi=300)
detect_and_display(image_generator)

Path(pdf_path).unlink()
