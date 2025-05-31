from flask import Flask, request, jsonify
import os
import gspread
from datetime import datetime
import logging
from gspread.exceptions import SpreadsheetNotFound, WorksheetNotFound
import json

app = Flask(__name__)
app.logger.setLevel(logging.INFO)

# Configurations
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "sivasakthiNo1")
SPREADSHEET_NAME = "OrdersSheet"
WORKSHEET_NAME = "Orders"
YOUR_EMAIL = "sivasakthisupermartpteltd@gmail.com" # Your email for spreadsheet access

# Load Google Sheets credentials from environment variable
SERVICE_ACCOUNT_JSON = os.getenv('{"type":"service_account","project_id":"imperial-berm-461507-i9","private_key_id":"21d40f5b632ac605ce4590fec150009edc8d93de","private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCmfzkpDXZDg7tm\nQMA2GrO8faYBJlI694Z6U4pfGNqnNeDKHBVKcaA7bha4HSdto/rncNJzcqm6uDVR\nCL8VqWXHaBd0m9WkYYuRHCmqKTIBPCqkCk38dg1UfAN0BFf90UJZ46f0zTgk17oM\nBFGAw1o/ia0/0i+k0nVWb5M0t+whoWN8Bjgm0jolta8kagsmONkWX7rq85NCSieC\neJuROhAiED7nktM+CfFQBBlO+aNNhxCuRj3U+FLCULzCNYJeYayAAM+nORV3q6Rl\nXc4I5PVgz8yyEpQH1EujkjHmtrFQ+8SOz4B/9urFkCckIdK8Lz//t2JRTDPVUO+G\n4SEq9BD7AgMBAAECggEAHAAKT16dtHX7dpNOH+s2rezdlZTpwFPvUDQrcZm+797u\nOl8lr3rTbRszA+yXPGeW4wREyDiQ1b9z6/hSFmUCIlpdk3U/pSDodVNsqFq8N5v0\nOdkny1zZGguvEvxGBgACrhZMoS1AE2YaOjohsMtpqoTPV4vUCl6AcDRcZ8HEmtUB\nahj711NqHf3eBJ/xtBo7cxsLyLlcGArQe7h1E74dmRynTUj5cL+xAQaClaRAqZ5q\nN0nY4oY3NjLIXiyu87gkLgfM59+/6YIp50RsgiU140qMuBkwU979EDUz1RJs8TAU\nzcJJEEbDNZgAahEErLDYBUIf/tqb3RwJ0RxzaKk1YQKBgQDVADLpS2tbU/D1nrZB\neAbGTyIrgZMmm1HV3s1vhw29wjTHvdguzF/+FHzUUFti9EG8pl4QxFJRnNJObiXQ\nLo2ukSY/+wCNYUDnUDsEmLmaxW6Y3bt8DzkPZBLKrj2pxyM3+LlISBaYiUkqBekl\nJMUjjD5hKelC2GO4Abq7tixeGwKBgQDIG7mG8Z/cJoODhNgA0jAWEZdcD7RHgJy4\nqdBLQ6UJs9Rw83yhu5rhnwW3bp/G/Sk6HbdHSqsBJgFH1H7h3/J38TM+oOfPWsjq\ndXC+NMWhCzWI61lZMStQ5H+Zhk0y+4gRESqVHVHhRc6l1AL7hqHgAtz7C6mJKCG5\nVY0MjQzGoQKBgQDF+21XE9cyCJAMff2CVQJXCe8E6WfRlsU2OeZSKAJJw14z2u46\ncZU4Ier1ncuT6t2/cBQ3GYQ6f72rUQ6sttjSze/zwGb/AsrFNvnkh+DdT25BgLhn\n0+6Bs88TvWlricHeoL33xanbFqB/Awd2kvr607yXq9E5ZNErk8/x8p7CyQKBgQCm\nURTEKbMaQRBxkUoOdKPu07QfmhXWj/iyKsGqrJBRHhvlvRnLOqgh+g/AQ7ucofFQ\nEj6wjEjQ7YuG7gB/L6jRM7HJzeadGvF+nRmVnTrc/PoD0Mg0L3+2/hNnwI4NX63Z\nsZDY2sOhHmoAvdO0xlNoYjjUlv7Ttn1BEu/mjJ0fwQKBgEXFEk59TxBOPV9DjjnA\ncXrQmXKnaHiFiijsaffdGjShsVnAJAhvYkNPF+v79ov5/AUGgYww8QmBB6b47oCY\nlLCzBURfPwzr5Py+Pe7a3ZXghU56s/QeBf2J06hN58iKQ/+3EIdt/V9NNMncxbFy\nCfeGCxBCGa1h6phvd3A1LBAd\n-----END PRIVATE KEY-----\n", "client_email": "whatsapporder@imperial-berm-461507-i9.iam.gserviceaccount.com","client_id": "108575719465985161811", "auth_uri": "https://accounts.google.com/o/oauth2/auth",  "token_uri": "https://oauth2.googleapis.com/token", "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/whatsapporder%40imperial-berm-461507-i9.iam.gserviceaccount.com", "universe_domain": "googleapis.com"}')
if not SERVICE_ACCOUNT_JSON:
    app.logger.error("GOOGLE_SERVICE_ACCOUNT_JSON environment variable not set")
    SERVICE_ACCOUNT_INFO = None
else:
    try:
        SERVICE_ACCOUNT_INFO = json.loads(SERVICE_ACCOUNT_JSON)
    except json.JSONDecodeError as e:
        app.logger.error(f"Error parsing service account JSON: {str(e)}")
        SERVICE_ACCOUNT_INFO = None

def get_sheet():
    """Get or create spreadsheet/worksheet"""
    if not SERVICE_ACCOUNT_INFO:
        raise RuntimeError("Google service account info not available")
    
    try:
        gc = gspread.service_account_from_dict(SERVICE_ACCOUNT_INFO)
    except Exception as e:
        app.logger.error(f"Google authentication failed: {str(e)}")
        raise
    
    try:
        # Open existing spreadsheet
        spreadsheet = gc.open(SPREADSHEET_NAME)
    except SpreadsheetNotFound:
        # Create new spreadsheet
        spreadsheet = gc.create(SPREADSHEET_NAME)
        # Share with yourself for easy access
        spreadsheet.share(YOUR_EMAIL, perm_type='user', role='writer')
        app.logger.info(f"Created new spreadsheet: {SPREADSHEET_NAME}")
    
    try:
        # Get existing worksheet
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
    except WorksheetNotFound:
        # Create new worksheet
        worksheet = spreadsheet.add_worksheet(
            title=WORKSHEET_NAME, 
            rows=1000, 
            cols=20
        )
        # Set headers
        worksheet.append_row(["Timestamp", "Sender", "Message", "Status"])
        app.logger.info(f"Created new worksheet: {WORKSHEET_NAME}")
    
    return worksheet

@app.route('/')
def home():
    return 'WhatsApp Order Processor Running'

# WhatsApp verification endpoint
@app.route('/webhook', methods=['GET'])
def whatsapp_verify():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    if mode and token == VERIFY_TOKEN:
        if mode == 'subscribe':
            app.logger.info("WhatsApp verification successful")
            return challenge, 200
    app.logger.warning("WhatsApp verification failed")
    return 'Verification failed', 403

# Order processing endpoint
@app.route('/webhook', methods=['POST'])
def whatsapp_webhook():
    try:
        data = request.get_json()
        app.logger.info("Received WhatsApp webhook")
        
        # Extract message details
        entry = data['entry'][0]['changes'][0]['value']
        message = entry['messages'][0]
        
        # Process only text messages
        if message['type'] == 'text':
            order_data = {
                'timestamp': datetime.fromtimestamp(int(message['timestamp'])).strftime('%Y-%m-%d %H:%M:%S'),
                'sender': message['from'],
                'message': message['text']['body'],
                'status': 'NEW ORDER'
            }
            
            # Save to Google Sheets
            sheet = get_sheet()
            sheet.append_row([
                order_data['timestamp'],
                order_data['sender'],
                order_data['message'],
                order_data['status']
            ])
            
            app.logger.info(f"Order saved from {order_data['sender']}")
            return jsonify({'status': 'success'}), 200
        
        return jsonify({'status': 'ignored, not text message'}), 200
        
    except Exception as e:
        app.logger.error(f"Processing error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
