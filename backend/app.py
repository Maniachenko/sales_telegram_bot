import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
from datetime import datetime
import fitz  # PyMuPDF
from PIL import Image

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

UPLOAD_FOLDER = 'uploads'
ITEM_DETECTION_FOLDER = 'item_detection_files'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(ITEM_DETECTION_FOLDER):
    os.makedirs(ITEM_DETECTION_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# List of shop names
shops = [
    {"name": "Albert Supermarket"},
    {"name": "Albert Hypermarket"},
    {"name": "CBA Premium"},
    {"name": "CBA Potraviny"},
    {"name": "CBA Market"},
    {"name": "Flop"},
    {"name": "Flop Top"},
    {"name": "Kaufland"},
    {"name": "Makro"},
    {"name": "Ratio"},
    {"name": "Tesco Hypermarket"},
    {"name": "Tesco Supermarket"},
    {"name": "Bene"},
    {"name": "EsoMarket"},
    {"name": "Globus"},
    {"name": "Tamda Foods"},
    {"name": "Prodejny Zeman"},
    {"name": "Billa"},
    {"name": "Lidl"},
    {"name": "Lidl Shop"},
    {"name": "Penny"},
    {"name": "Travel Free"},
    {"name": "Zeman"}
]

# Storage for uploaded PDF data
pdf_data_file = 'pdf_data.json'
if not os.path.exists(pdf_data_file):
    with open(pdf_data_file, 'w') as f:
        json.dump([], f)


def load_pdf_data():
    with open(pdf_data_file, 'r') as f:
        return json.load(f)


def save_pdf_data(data):
    with open(pdf_data_file, 'w') as f:
        json.dump(data, f, indent=4)


def get_unique_filename(filepath):
    """
    Generate a unique filename by appending a number if the file already exists.
    """
    base, ext = os.path.splitext(filepath)
    counter = 1
    new_filepath = filepath
    while os.path.exists(new_filepath):
        new_filepath = f"{base}_{counter}{ext}"
        counter += 1
    return new_filepath


@app.route('/shops', methods=['GET'])
def get_shops():
    return jsonify(shops)


@app.route('/pdfs', methods=['GET'])
def get_pdfs():
    pdf_data = load_pdf_data()
    return jsonify(pdf_data)


@app.route('/upload', methods=['POST'])
def upload_file():
    shop_name = request.form.get('shop_name')
    valid_from = request.form.get('valid_from')
    valid_to = request.form.get('valid_to')
    file = request.files.get('file')
    file_url = request.form.get('file_url')

    # Check if all required fields are provided
    if not shop_name or not valid_from or not valid_to:
        return jsonify({"error": "Shop name, valid from, and valid to dates are required"}), 400

    if file:
        filename = file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        filepath = get_unique_filename(filepath)
        file.save(filepath)
    elif file_url:
        try:
            response = requests.get(file_url)
            if '%' in file_url:
                filename = file_url.split('%')[-1]
            else:
                filename = file_url.split('/')[-1]
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            filepath = get_unique_filename(filepath)
            with open(filepath, 'wb') as f:
                f.write(response.content)
        except Exception as e:
            return jsonify({"error": f"Failed to download file from URL: {str(e)}"}), 400
    else:
        return jsonify({"error": "No file provided"}), 400

    pdf_entry = {
        "shop_name": shop_name,
        "filename": os.path.basename(filepath),
        "valid_from": valid_from,
        "valid_to": valid_to,
        "upload_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "used": False  # Default to False
    }

    pdf_data = load_pdf_data()
    pdf_data.append(pdf_entry)
    save_pdf_data(pdf_data)

    return jsonify({"message": "File uploaded successfully", "filepath": filepath}), 200


@app.route('/update/<filename>', methods=['POST'])
def update_file(filename):
    pdf_data = load_pdf_data()
    for entry in pdf_data:
        if entry['filename'] == filename:
            entry['shop_name'] = request.form.get('shop_name')
            entry['valid_from'] = request.form.get('valid_from')
            entry['valid_to'] = request.form.get('valid_to')

            new_file = request.files.get('file')
            new_file_url = request.form.get('file_url')
            if new_file:
                new_filename = new_file.filename
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
                filepath = get_unique_filename(filepath)
                new_file.save(filepath)
                entry['filename'] = os.path.basename(filepath)
            elif new_file_url:
                try:
                    response = requests.get(new_file_url)
                    if '%' in new_file_url:
                        new_filename = new_file_url.split('%')[-1]
                    else:
                        new_filename = new_file_url.split('/')[-1]
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
                    filepath = get_unique_filename(filepath)
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    entry['filename'] = os.path.basename(filepath)
                except Exception as e:
                    return jsonify({"error": f"Failed to download file from URL: {str(e)}"}), 400

            save_pdf_data(pdf_data)
            return jsonify({"message": "File updated successfully"}), 200

    return jsonify({"error": "File not found"}), 404


@app.route('/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    pdf_data = load_pdf_data()
    new_pdf_data = [entry for entry in pdf_data if entry['filename'] != filename]

    if len(new_pdf_data) == len(pdf_data):
        return jsonify({"error": "File not found"}), 404

    save_pdf_data(new_pdf_data)

    # Delete file from the uploads folder
    try:
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    except OSError as e:
        return jsonify({"error": f"Failed to delete file: {str(e)}"}), 400

    return jsonify({"message": "File deleted successfully"}), 200


@app.route('/uploads/<filename>', methods=['GET'])
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/import_item_detection', methods=['POST'])
def import_item_detection():
    pdf_data = load_pdf_data()
    updated = False
    for entry in pdf_data:
        if not entry.get('used', False):
            pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], entry['filename'])
            if not os.path.exists(pdf_path):
                continue

            # Create a directory for the JPEG files
            date_str = datetime.now().strftime('%Y%m%d')
            detection_folder = os.path.join(ITEM_DETECTION_FOLDER, f'files_{date_str}')
            if not os.path.exists(detection_folder):
                os.makedirs(detection_folder)

            # Open the PDF file
            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap()
                jpeg_filename = f"{os.path.splitext(entry['filename'])[0]}_{page_num + 1}.jpeg"
                jpeg_filepath = os.path.join(detection_folder, jpeg_filename)
                pix.save(jpeg_filepath)

            entry['used'] = True
            updated = True

    if updated:
        save_pdf_data(pdf_data)
        return jsonify({"message": "All applicable files marked as used and pages extracted."}), 200
    else:
        return jsonify({"message": "No files to update."}), 200


if __name__ == '__main__':
    app.run(debug=True)
