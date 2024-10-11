import json
import os
from flask import Flask, request, jsonify
import cv2
import logging

import base64
import tempfile
from ultralytics import YOLO
from transformers import AutoModel, AutoTokenizer

# Initialize the YOLO models
model1 = YOLO('./item_detector/best.pt')  # CPU by default
model2 = YOLO('./item_processor/best.pt')  # CPU by default

# Initialize the GOT-OCR2_0 model
tokenizer = AutoTokenizer.from_pretrained('stepfun-ai/GOT-OCR2_0', trust_remote_code=True)
got_model = AutoModel.from_pretrained('stepfun-ai/GOT-OCR2_0',
                                      trust_remote_code=True,
                                      low_cpu_mem_usage=True,
                                      device_map='cuda',
                                      use_safetensors=True,
                                      pad_token_id=tokenizer.eos_token_id).eval().cuda()

app = Flask(__name__)
# Configure the logger
logging.basicConfig(
    level=logging.INFO,  # Set the logging level (e.g., DEBUG, INFO, WARNING, ERROR)
    format='%(asctime)s - %(levelname)s - %(message)s',  # Log message format
    handlers=[logging.StreamHandler()]  # Log to console (can add file handler here too)
)

# Get a logger instance
logger = logging.getLogger(__name__)


# Helper function to predict using YOLO model
def predict(chosen_model, img, classes=[], conf=0.5):
    """Predict using YOLO model."""
    if classes:
        results = chosen_model.predict(img, classes=classes, conf=conf, device='cpu')  # Use CPU
    else:
        results = chosen_model.predict(img, conf=conf, device='cpu')  # Use CPU
    return results


# Helper function to detect and draw bounding boxes
def predict_and_detect(chosen_model, img, classes=[], conf=0.5):
    """Detect and draw bounding boxes with class names."""
    results = predict(chosen_model, img, classes, conf)
    for result in results:
        for box in result.boxes:
            # Draw bounding boxes
            cv2.rectangle(img,
                          (int(box.xyxy[0][0]), int(box.xyxy[0][1])),
                          (int(box.xyxy[0][2]), int(box.xyxy[0][3])),
                          (255, 0, 0), 2)
            # Add class names
            cv2.putText(img, f"{result.names[int(box.cls[0])]}",
                        (int(box.xyxy[0][0]), int(box.xyxy[0][1]) - 10),
                        cv2.FONT_HERSHEY_PLAIN, 1, (255, 0, 0), 1)
    return img, results


# Helper function to encode image as base64 string
def image_to_base64(img):
    _, buffer = cv2.imencode('.png', img)  # Encode the image as PNG
    return base64.b64encode(buffer).decode('utf-8')  # Return base64 encoded string


# OCR function using GOT-OCR2_0 model and chat interface
def extract_text_from_image(image_path):
    """
    Extract text from an image using the GOT-OCR2_0 model's chat interface.
    """
    try:
        # Run the OCR chat model on the image path (use tokenizer and model as before)
        extracted_text = got_model.chat(tokenizer, image_path, ocr_type='ocr')
        return extracted_text
    except Exception as e:
        raise Exception(f"Exception in extract_text_from_image: {e}")


# OCR function using GOT-OCR2_0 model and bounding boxes
def extract_text_from_image_with_box(image_path, box):
    """
    Extract text from an image using the GOT-OCR2_0 model's chat interface with a bounding box.
    """
    try:
        # Convert the box (list of integers) to a string format expected by the model
        ocr_box_str = '[' + ','.join(map(str, box)) + ']'

        # Fine-grained OCR using bounding box
        extracted_text = got_model.chat(tokenizer, image_path, ocr_type='ocr', ocr_box=ocr_box_str)
        return extracted_text
    except Exception as e:
        raise Exception(f"Exception in extract_text_from_image_with_box: {e}")


# API route to run YOLO on an uploaded image
@app.route('/predict', methods=['POST'])
def run_yolo():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400

    # Use a temporary file to store the image
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_img_file:
        # Load the image file from the request
        image_file = request.files['image']
        image_file.save(temp_img_file.name)
        temp_img_path = temp_img_file.name

    try:
        # Read the image using OpenCV
        img = cv2.imread(temp_img_path)

        # Select model based on query param, default to model1
        chosen_model = request.args.get('model', 'model1')
        if chosen_model == 'model1':
            model = model1
        else:
            model = model2

        # Run YOLO detection on the image
        detected_img, results = predict_and_detect(model, img, conf=0.5)

        # Convert image to base64
        base64_image = image_to_base64(detected_img)

        # Convert results into JSON format
        result_data = []
        for result in results:
            for box in result.boxes:
                result_data.append({
                    'class': result.names[int(box.cls[0])],
                    'confidence': box.conf[0].item(),
                    'box': [int(box.xyxy[0][0]), int(box.xyxy[0][1]), int(box.xyxy[0][2]), int(box.xyxy[0][3])]
                })

        return jsonify({'detections': result_data, 'image': base64_image}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        # Clean up: Delete the temporary image file
        os.remove(temp_img_path)


# API route for text extraction using GOT-OCR2_0
@app.route('/extract_text', methods=['POST'])
def extract_text():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400

    # Use a temporary file to store the image
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_img_file:
        image_file = request.files['image']
        image_file.save(temp_img_file.name)
        temp_img_path = temp_img_file.name

    try:
        # Extract text using GOT-OCR2_0 model's chat interface
        extracted_text = extract_text_from_image(temp_img_path)

        return jsonify({'extracted_text': extracted_text}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        # Clean up: Delete the temporary image file
        os.remove(temp_img_path)


@app.route('/extract_text_with_box', methods=['POST'])
def extract_text_with_box():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400

    # Parse the JSON payload correctly
    try:
        json_data = json.loads(request.form.get('json'))
        box = json_data.get('box')
        if not box:
            logger.error("No bounding box provided")
            return jsonify({'error': 'No bounding box provided'}), 400
    except Exception as e:
        logger.error(f"Failed to parse JSON data: {e}")
        return jsonify({'error': 'Invalid or missing JSON data'}), 400

    logger.info(f"Received bounding box: {box}")

    # Proceed with processing the image and the bounding box...

    # Process the image and bounding box
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_img_file:
        image_file = request.files['image']
        image_file.save(temp_img_file.name)
        temp_img_path = temp_img_file.name

    try:
        # Extract text using GOT-OCR2_0 model's chat interface
        extracted_text = extract_text_from_image_with_box(temp_img_path, box)
        logger.info(f"Extracted text: {extracted_text}")

        return jsonify({'extracted_text': extracted_text}), 200

    except Exception as e:
        logger.error(f"Exception in extract_text_with_box: {e}")
        return jsonify({'error': str(e)}), 500

    finally:
        os.remove(temp_img_path)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)