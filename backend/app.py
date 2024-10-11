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

# Helper functions
def create_s3_bucket():
    """Creates an S3 bucket if it does not already exist."""
    try:
        s3.head_bucket(Bucket=BUCKET_NAME)
        logging.info(f"S3 bucket {BUCKET_NAME} already exists.")
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code in ('404', 'NoSuchBucket'):
            try:
                s3.create_bucket(
                    Bucket=BUCKET_NAME,
                    CreateBucketConfiguration={'LocationConstraint': AWS_REGION}
                )
                logging.info(f"S3 bucket {BUCKET_NAME} created successfully.")
            except ClientError as ce:
                logging.error(f"Error creating the bucket: {ce}")
        elif error_code == '301':
            logging.error(f"S3 bucket {BUCKET_NAME} exists in a different region.")
        else:
            logging.error(f"Error checking for the bucket: {e}")


def create_dynamodb_table():
    """Creates a DynamoDB table if it does not already exist."""
    try:
        table = dynamodb.Table(TABLE_NAME)
        table.load()
        logging.info(f"Table {TABLE_NAME} already exists.")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            logging.info(f"Table {TABLE_NAME} does not exist. Creating it now...")
            table = dynamodb.create_table(
                TableName=TABLE_NAME,
                KeySchema=[
                    {'AttributeName': 'filename', 'KeyType': 'HASH'},
                    {'AttributeName': 'shop_name', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'filename', 'AttributeType': 'S'},
                    {'AttributeName': 'shop_name', 'AttributeType': 'S'}
                ],
                ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            )
            table.meta.client.get_waiter('table_exists').wait(TableName=TABLE_NAME)
            logging.info(f"Table {TABLE_NAME} created successfully.")
        else:
            logging.error(f"Error checking for the table: {e}")


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

        pdf_entry = {
            "shop_name": shop_name,
            "filename": filename,
            "s3_url": s3_url,
            "valid_from": valid_from,
            "valid_to": valid_to,
            "upload_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "page_split": False,
            "used": False
        }
        pdf_data = load_pdf_data()
        pdf_data.append(pdf_entry)
        save_pdf_data(pdf_data)

        return jsonify({"message": "File uploaded successfully", "filename": filename, "s3_url": s3_url}), 200

    except NoCredentialsError:
        return jsonify({"error": "AWS credentials not available"}), 500


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


# Start the Flask app
if __name__ == '__main__':
    create_s3_bucket()
    create_dynamodb_table()
    app.run(debug=True)
