import os
import cv2
import warnings
from PIL import Image
from transformers import AutoModel, AutoTokenizer
import json
import numpy as np
from tqdm import tqdm

# Suppress warnings
warnings.filterwarnings("ignore")

# Load GOT-OCR2_0 model and tokenizer
tokenizer = AutoTokenizer.from_pretrained('stepfun-ai/GOT-OCR2_0', trust_remote_code=True)
got_model = AutoModel.from_pretrained('stepfun-ai/GOT-OCR2_0',
                                      trust_remote_code=True,
                                      low_cpu_mem_usage=True,
                                      device_map='cuda',
                                      use_safetensors=True,
                                      pad_token_id=tokenizer.eos_token_id).eval().cuda()

# Paths
base_data_dir = './item_processing/data'
output_json_path = './detected_items.json'

# Ensure the output JSON file exists
if not os.path.exists(output_json_path):
    with open(output_json_path, 'w') as json_file:
        json.dump([], json_file)

# Collect all image files recursively
image_files = [os.path.join(root, file) for root, _, files in os.walk(base_data_dir)
               for file in files if file.lower().endswith(('.jpg', '.jpeg', '.png'))]

# Process each image with progress bar
with tqdm(total=len(image_files), desc="Processing images", unit="image") as pbar:
    for image_path in image_files:
        image_file = os.path.basename(image_path)
        image_dir = os.path.dirname(image_path)

        # Load the image
        image = cv2.imread(image_path)
        if image is None:
            print(f"Failed to load image: {image_path}")
            pbar.update(1)
            continue

        height, width, _ = image.shape

        # Construct label file path
        label_file_name = os.path.splitext(image_file)[0] + '.txt'
        label_dir = image_dir.replace('images', 'labels') if 'images' in image_dir else image_dir
        label_path = os.path.join(label_dir, label_file_name)

        if not os.path.exists(label_path):
            pbar.update(1)
            continue

        # Prepare data for this image
        image_data = {
            "image_name": image_file,
            "detected_objects": []
        }

        # Load the label file and process each detected object
        with open(label_path, 'r') as f:
            for line in f.readlines():
                parts = line.strip().split()
                if len(parts) < 5:
                    continue
                class_id = int(parts[0])
                x_center, y_center, bbox_width, bbox_height = map(float, parts[1:5])

                # Convert relative to absolute coordinates
                x_center_abs = x_center * width
                y_center_abs = y_center * height
                bbox_width_abs = bbox_width * width
                bbox_height_abs = bbox_height * height

                x1 = int(x_center_abs - bbox_width_abs / 2)
                y1 = int(y_center_abs - bbox_height_abs / 2)
                x2 = int(x_center_abs + bbox_width_abs / 2)
                y2 = int(y_center_abs + bbox_height_abs / 2)

                # Ensure coordinates are within image bounds
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(width - 1, x2), min(height - 1, y2)

                if x1 >= x2 or y1 >= y2:
                    continue

                # Crop the detected area and convert to PIL Image
                cropped_image = image[y1:y2, x1:x2]
                if cropped_image.size == 0:
                    continue

                pil_image = Image.fromarray(cv2.cvtColor(cropped_image, cv2.COLOR_BGR2RGB))

                # Temporarily save cropped image for OCR
                cropped_image_path = './cropped_temp.jpg'
                pil_image.save(cropped_image_path)

                # Perform OCR using GOT-OCR2_0
                got_text = got_model.chat(tokenizer, cropped_image_path, ocr_type='ocr')

                # Store detected object data
                detected_object = {
                    "coordinates": [x1, y1, x2, y2],
                    "class_id": class_id,
                    "got_ocr_text": got_text
                }
                image_data["detected_objects"].append(detected_object)

        if image_data["detected_objects"]:
            # Append detected items to the JSON file
            with open(output_json_path, 'r+') as json_file:
                detected_items = json.load(json_file)
                detected_items.append(image_data)
                json_file.seek(0)
                json.dump(detected_items, json_file, indent=4)

        # Cleanup temporary file and update progress bar
        if os.path.exists(cropped_image_path):
            os.remove(cropped_image_path)

        pbar.update(1)
