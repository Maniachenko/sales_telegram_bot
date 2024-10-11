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

# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)


def predict(model, img, classes=[], conf=0.5):
    """
    Predict objects in the image using a specified YOLO model.

    :param model: The YOLO model to use for prediction.
    :param img: The image to run predictions on.
    :param classes: Optional; List of class indices to filter the predictions by.
    :param conf: Optional; Confidence threshold for predictions. Default is 0.5.

    :return: YOLO model prediction results.
    """
    return model.predict(img, classes=classes, conf=conf, device='cpu')


def predict_and_detect(model, img, classes=[], conf=0.5):
    """
    Detect objects and draw bounding boxes on the image with class labels.

    :param model: The YOLO model to use for detection.
    :param img: The image to detect objects on.
    :param classes: Optional; List of class indices to filter the detection by.
    :param conf: Optional; Confidence threshold for detection. Default is 0.5.

    :return: Tuple of the modified image with bounding boxes and the YOLO model prediction results.
    """
    results = predict(model, img, classes, conf)
    for result in results:
        for box in result.boxes:
            cv2.rectangle(img, (int(box.xyxy[0][0]), int(box.xyxy[0][1])),
                          (int(box.xyxy[0][2]), int(box.xyxy[0][3])), (255, 0, 0), 2)
            cv2.putText(img, f"{result.names[int(box.cls[0])]}",
                        (int(box.xyxy[0][0]), int(box.xyxy[0][1]) - 10),
                        cv2.FONT_HERSHEY_PLAIN, 1, (255, 0, 0), 1)
    return img, results


def image_to_base64(img):
    """
    Encode the image as a base64 string.

    :param img: The image to encode.

    :return: Base64 encoded string of the image.
    """
    _, buffer = cv2.imencode('.png', img)
    return base64.b64encode(buffer).decode('utf-8')


def extract_text_from_image(image_path):
    """
    Extract text from an image using the GOT-OCR2_0 model.

    :param image_path: The file path to the image for OCR.

    :return: Extracted text from the image.
    :raises Exception: If an error occurs during the OCR process.
    """
    try:
        return got_model.chat(tokenizer, image_path, ocr_type='ocr')
    except Exception as e:
        raise Exception(f"Error in extract_text_from_image: {e}")


def extract_text_from_image_with_box(image_path, box):
    """
    Extract text from an image within a specific bounding box using the GOT-OCR2_0 model.

    :param image_path: The file path to the image for OCR.
    :param box: List of coordinates defining the bounding box [x_min, y_min, x_max, y_max].

    :return: Extracted text from the bounding box in the image.
    :raises Exception: If an error occurs during the OCR process.
    """
    try:
        ocr_box_str = '[' + ','.join(map(str, box)) + ']'
        return got_model.chat(tokenizer, image_path, ocr_type='ocr', ocr_box=ocr_box_str)
    except Exception as e:
        raise Exception(f"Error in extract_text_from_image_with_box: {e}")


@app.route('/predict', methods=['POST'])
def run_yolo():
    """
    API endpoint to run YOLO detection on an uploaded image.

    :return: JSON response containing the detection results and base64-encoded image.
    :raises ValueError: If no image is uploaded or an error occurs during processing.
    """
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_img_file:
        request.files['image'].save(temp_img_file.name)
        temp_img_path = temp_img_file.name

    try:
        img = cv2.imread(temp_img_path)
        chosen_model = model1 if request.args.get('model', 'model1') == 'model1' else model2
        detected_img, results = predict_and_detect(chosen_model, img, conf=0.5)

        result_data = [{'class': result.names[int(box.cls[0])],
                        'confidence': box.conf[0].item(),
                        'box': [int(box.xyxy[0][0]), int(box.xyxy[0][1]), int(box.xyxy[0][2]), int(box.xyxy[0][3])]}
                       for result in results for box in result.boxes]

        return jsonify({'detections': result_data, 'image': image_to_base64(detected_img)}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        os.remove(temp_img_path)


@app.route('/extract_text', methods=['POST'])
def extract_text():
    """
    API endpoint to extract text from an uploaded image using the GOT-OCR2_0 model.

    :return: JSON response containing the extracted text.
    :raises ValueError: If no image is uploaded or an error occurs during the OCR process.
    """
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_img_file:
        request.files['image'].save(temp_img_file.name)
        temp_img_path = temp_img_file.name

    try:
        extracted_text = extract_text_from_image(temp_img_path)
        return jsonify({'extracted_text': extracted_text}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        os.remove(temp_img_path)


@app.route('/extract_text_with_box', methods=['POST'])
def extract_text_with_box():
    """
    API endpoint to extract text from a specific bounding box in an uploaded image using the GOT-OCR2_0 model.

    :return: JSON response containing the extracted text from the bounding box.
    :raises ValueError: If no image or bounding box is uploaded or an error occurs during the OCR process.
    """
    if 'image' not in request.files or not request.form.get('json'):
        return jsonify({'error': 'No image or JSON uploaded'}), 400

    try:
        json_data = json.loads(request.form.get('json'))
        box = json_data.get('box')
        if not box:
            logger.error("No bounding box provided")
            return jsonify({'error': 'No bounding box provided'}), 400

        logger.info(f"Received bounding box: {box}")
    except Exception as e:
        logger.error(f"Failed to parse JSON data: {e}")
        return jsonify({'error': 'Invalid JSON data'}), 400

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_img_file:
        request.files['image'].save(temp_img_file.name)
        temp_img_path = temp_img_file.name

    try:
        extracted_text = extract_text_from_image_with_box(temp_img_path, box)
        return jsonify({'extracted_text': extracted_text}), 200

    except Exception as e:
        logger.error(f"Error in extract_text_with_box: {e}")
        return jsonify({'error': str(e)}), 500

    finally:
        os.remove(temp_img_path)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)