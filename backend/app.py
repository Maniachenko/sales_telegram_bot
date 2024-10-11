import logging
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
from datetime import datetime
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from airflow.api.client.local_client import Client

# AWS and Airflow configurations
dynamodb = boto3.resource('dynamodb')
TABLE_NAME = 'pdf_metadata'
BUCKET_NAME = 'salestelegrambot'
AWS_REGION = 'eu-west-1'
AIRFLOW_URL = 'http://localhost:8080/api/v1'
AIRFLOW_DAG_ID = 'pages_data_pipeline'

s3 = boto3.client('s3', region_name=AWS_REGION)

# Flask app setup
app = Flask(__name__)
CORS(app)

# Constants
UPLOAD_FOLDER = 'uploads'
ITEM_DETECTION_FOLDER = 'item_detection_files'
ITEM_PROCESSING_FOLDER = 'item_processing_files'
pdf_data_file = 'pdf_data.json'

# Ensure necessary directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(ITEM_DETECTION_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# List of shops
shops = [
    {"name": "Albert Supermarket"}, {"name": "Albert Hypermarket"}, {"name": "CBA Premium"},
    {"name": "CBA Potraviny"}, {"name": "CBA Market"}, {"name": "Flop"}, {"name": "Flop Top"},
    {"name": "Kaufland"}, {"name": "Makro"}, {"name": "Ratio"}, {"name": "Tesco Hypermarket"},
    {"name": "Tesco Supermarket"}, {"name": "Bene"}, {"name": "EsoMarket"}, {"name": "Globus"},
    {"name": "Tamda Foods"}, {"name": "Prodejny Zeman"}, {"name": "Billa"}, {"name": "Lidl"},
    {"name": "Lidl Shop"}, {"name": "Penny"}, {"name": "Travel Free"}, {"name": "Zeman"}
]


def load_pdf_data():
    """Load PDF metadata from DynamoDB."""
    try:
        response = dynamodb.Table(TABLE_NAME).scan()
        return response.get('Items', [])
    except Exception as e:
        logging.error(f"Error loading data from DynamoDB: {e}")
        return []


def save_pdf_data(data):
    """Save PDF metadata to DynamoDB."""
    table = dynamodb.Table(TABLE_NAME)
    try:
        for entry in data:
            table.put_item(Item=entry)
    except Exception as e:
        logging.error(f"Error saving data to DynamoDB: {e}")


def get_unique_filename(filepath):
    """Generate a unique filename if the file already exists."""
    base, ext = os.path.splitext(filepath)
    counter = 1
    new_filepath = filepath
    while os.path.exists(new_filepath):
        new_filepath = f"{base}_{counter}{ext}"
        counter += 1
    return new_filepath


# Endpoints
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

    if not shop_name or not valid_from or not valid_to:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        if file:
            filename = file.filename
            s3.upload_fileobj(file, BUCKET_NAME, f'pdfs/{filename}')
            s3_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/pdfs/{filename}"
        elif file_url:
            response = requests.get(file_url)
            filename = file_url.split('/')[-1].split('?')[0]
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            with open(file_path, 'wb') as f:
                f.write(response.content)
            with open(file_path, 'rb') as f:
                s3.upload_fileobj(f, BUCKET_NAME, f'pdfs/{filename}')
            s3_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/pdfs/{filename}"
        else:
            return jsonify({"error": "Either file or file_url must be provided"}), 400

        # Convert valid_from and valid_to to date objects
        valid_from_date = datetime.strptime(valid_from, '%Y-%m-%d').date()
        valid_to_date = datetime.strptime(valid_to, '%Y-%m-%d').date()

        # Get today's date
        today = datetime.utcnow().date()

        # Determine if the PDF is valid based on the current date
        is_valid = valid_from_date <= today <= valid_to_date

        pdf_entry = {
            "shop_name": shop_name,
            "filename": filename,
            "s3_url": s3_url,
            "valid_from": valid_from,
            "valid_to": valid_to,
            "upload_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "page_split": False,
            "used": False,
            "valid": is_valid
        }
        pdf_data = load_pdf_data()
        pdf_data.append(pdf_entry)
        save_pdf_data(pdf_data)

        return jsonify(
            {"message": "File uploaded successfully", "filename": filename, "s3_url": s3_url, "valid": is_valid}), 200

    except NoCredentialsError:
        return jsonify({"error": "AWS credentials not available"}), 500


@app.route('/update/<filename>', methods=['POST'])
def update_file(filename):
    try:
        # Load the current PDF data from DynamoDB
        pdf_data = load_pdf_data()

        # Find the entry for the specified filename
        file_entry = next((entry for entry in pdf_data if entry['filename'] == filename), None)

        if not file_entry:
            return jsonify({"error": "File not found"}), 404

        # Get the incoming data from the request
        shop_name = request.form.get('shop_name', file_entry['shop_name'])  # Default to existing value
        valid_from = request.form.get('valid_from', file_entry['valid_from'])
        valid_to = request.form.get('valid_to', file_entry['valid_to'])
        file = request.files.get('file')

        # Convert valid_from and valid_to to date objects
        valid_from_date = datetime.strptime(valid_from, '%Y-%m-%d').date()
        valid_to_date = datetime.strptime(valid_to, '%Y-%m-%d').date()

        # Get today's date
        today = datetime.utcnow().date()

        # Perform validity check based on the current date
        is_valid = valid_from_date <= today <= valid_to_date

        # Update file if a new one is provided
        if file:
            # Remove old file from S3
            s3.delete_object(Bucket=BUCKET_NAME, Key=f'pdfs/{filename}')

            # Upload new file to S3
            new_filename = file.filename
            s3.upload_fileobj(file, BUCKET_NAME, f'pdfs/{new_filename}')
            s3_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/pdfs/{new_filename}"
            file_entry['filename'] = new_filename
            file_entry['s3_url'] = s3_url

        # Update the metadata
        file_entry['shop_name'] = shop_name
        file_entry['valid_from'] = valid_from
        file_entry['valid_to'] = valid_to
        file_entry['valid'] = is_valid

        # Save updated entry back to DynamoDB
        save_pdf_data(pdf_data)

        return jsonify({"message": f"File {filename} updated successfully", "valid": is_valid}), 200

    except Exception as e:
        return jsonify({"error": f"Error updating file: {e}"}), 500


@app.route('/trigger_pipeline/<filename>', methods=['POST'])
def trigger_pipeline(filename):
    pdf_data = load_pdf_data()
    file_entry = next((entry for entry in pdf_data if entry['filename'] == filename), None)

    if not file_entry:
        return jsonify({"error": "File not found"}), 404

    payload = {'filename': filename, 'shop_name': file_entry['shop_name']}
    app.logger.debug(f"Triggering Airflow DAG with payload: {json.dumps(payload)}")

    try:
        client = Client(None, None)
        client.trigger_dag(dag_id=AIRFLOW_DAG_ID, run_id=None, conf=payload)

        file_entry['used'] = True
        save_pdf_data(pdf_data)

        return jsonify({"message": f"Pipeline triggered for {filename}"}), 200
    except Exception as e:
        app.logger.error(f"Failed to trigger Airflow DAG: {e}")
        return jsonify({"error": "Failed to trigger Airflow DAG"}), 500


@app.route('/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    try:
        # Load PDF data
        pdf_data = load_pdf_data()

        # Find the entry in the DynamoDB table
        file_entry = next((entry for entry in pdf_data if entry['filename'] == filename), None)

        if not file_entry:
            return jsonify({"error": "File not found"}), 404

        # Delete the file from S3
        s3.delete_object(Bucket=BUCKET_NAME, Key=f'pdfs/{filename}')

        # Remove the entry from DynamoDB
        table = dynamodb.Table(TABLE_NAME)
        table.delete_item(
            Key={
                'filename': filename,
                'shop_name': file_entry['shop_name']
            }
        )

        # Remove the file entry from the local pdf_data if applicable
        pdf_data = [entry for entry in pdf_data if entry['filename'] != filename]
        save_pdf_data(pdf_data)

        return jsonify({"message": f"File {filename} deleted successfully"}), 200

    except NoCredentialsError:
        return jsonify({"error": "AWS credentials not available"}), 500
    except Exception as e:
        return jsonify({"error": f"Error deleting file: {e}"}), 500


# Start the Flask app
if __name__ == '__main__':
    app.run(debug=True)
