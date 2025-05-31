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
SERVICE_ACCOUNT_JSON ="project/service_account.json"
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
