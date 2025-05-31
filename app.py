from flask import Flask, request, jsonify
import os
import gspread
from datetime import datetime
import logging
from gspread.exceptions import SpreadsheetNotFound, WorksheetNotFound

app = Flask(__name__)
app.logger.setLevel(logging.INFO)

# Configurations
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "sivasakthiNo1")
SPREADSHEET_NAME = "OrdersSheet"
WORKSHEET_NAME = "Orders"
YOUR_EMAIL = "sivasakthisupermartpteltd@gmail.com"

# Path to the secret service account file
SERVICE_ACCOUNT_FILE = "/etc/secrets/service_account.json"

def get_sheet():
    """Get or create spreadsheet/worksheet using secure file"""
    try:
        # Verify the secret file exists
        if not os.path.exists(SERVICE_ACCOUNT_FILE):
            app.logger.error(f"Service account file not found at {SERVICE_ACCOUNT_FILE}")
            raise RuntimeError("Service account credentials missing")
            
        # Authenticate using the service account file
        gc = gspread.service_account(SERVICE_ACCOUNT_FILE)
        app.logger.info("Google authentication successful")
    except Exception as e:
        app.logger.error(f"Google authentication failed: {str(e)}")
        raise
    
    try:
        # Open existing spreadsheet
        spreadsheet = gc.open(SPREADSHEET_NAME)
        app.logger.info(f"Opened spreadsheet: {SPREADSHEET_NAME}")
    except SpreadsheetNotFound:
        # Create new spreadsheet
        spreadsheet = gc.create(SPREADSHEET_NAME)
        # Share with yourself for easy access
        spreadsheet.share(YOUR_EMAIL, perm_type='user', role='writer')
        app.logger.info(f"Created new spreadsheet: {SPREADSHEET_NAME}")
    
    try:
        # Get existing worksheet
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
        app.logger.info(f"Opened worksheet: {WORKSHEET_NAME}")
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
    app.logger.warning(f"Verification failed. Received token: {token}, Expected: {VERIFY_TOKEN}")
    return 'Verification failed', 403

# Order processing endpoint
@app.route('/webhook', methods=['POST'])
def whatsapp_webhook():
    try:
        data = request.get_json()
        app.logger.info("Received WhatsApp webhook")
        
        # Validate webhook structure
        if 'entry' not in data or not data['entry']:
            return jsonify({'status': 'invalid format'}), 400
            
        entry = data['entry'][0]
        changes = entry.get('changes', [{}])[0]
        value = changes.get('value', {})
        
        # Process messages
        if 'messages' in value and value['messages']:
            message = value['messages'][0]
            if message.get('type') == 'text':
                order_data = {
                    'timestamp': datetime.fromtimestamp(int(message['timestamp'])).strftime('%Y-%m-%d %H:%M:%S'),
                    'sender': message['from'],
                    'message': message['text']['body'],
                    'status': 'NEW ORDER'
                }
                
                sheet = get_sheet()
                sheet.append_row([
                    order_data['timestamp'],
                    order_data['sender'],
                    order_data['message'],
                    order_data['status']
                ])
                
                # Mask sender in logs for privacy
                app.logger.info(f"Order saved from {order_data['sender'][:5]}...")
                return jsonify({'status': 'success'}), 200
        
        return jsonify({'status': 'ignored'}), 200
        
    except Exception as e:
        app.logger.error(f"Processing error: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Internal error'}), 500

if __name__ == '__main__':
    # Verify service account exists on startup
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        app.logger.critical("Service account file not found! Application cannot start")
    else:
        app.logger.info("Service account file verified")
    
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
