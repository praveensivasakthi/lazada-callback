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
VERIFY_TOKEN = os.getenv("sivasakthiNo1", "DEFAULT_SECRET_TOKEN")
SPREADSHEET_NAME = "OrdersSheet"
WORKSHEET_NAME = "Orders"
YOUR_EMAIL = "sivasakthisupermartpteltd@gmail.com"  # Replace with your email

# Load Google Sheets credentials from environment variable
SERVICE_ACCOUNT_JSON = os.getenv({"type":"service_account","project_id":"lexical-script-460408-a5","private_key_id":"4637b14d49dacca024ccac86f8688027c782659b","private_key":"-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC/Yy2q6nSXEnN/\nAtViWAy4lKPJnKrtY84ez8CgBqW5Kwq805Puk7g3RIgCIUsRLwoMU7B0KSMK7Sm9\nNs4iRJ0l5jrhKbU26zJ1HRCYhfBv0qlvWTm6tAETVw8HaZKYn7jsVk78zhI8vyg5\nY7rAIyZ9PcBJkHuALDWC2pC1Tl1f1uqPQaYoYXXm2AVgy9jnPJQFOldDsxoTHMq2\nVR7t9l4kyzC5YwjYbhmXxjt7Gbske+oDLMf46r11duQmgEXC2DRzmWJ+w5v30Ulw\ngYYlQY3Kxa40hLKuwGP1wO6yGaZl4reSYvJz2tBvfiFXCb6eJBqLjj3L30M03gFJ\ncEhn/K3fAgMBAAECggEAHzxIj8SEEsPoJaqIuOw150obESSIoQXQ9iZiAbwUAAyO\nTBMb6awiPKLqr65PWhabRTfDbLHqDjZ2wXLYYa9hFnZk1arA8J2iNorv0nTJsPZo\nwMuHKHmIU2e6BDOuwUoQHEJZ0diwEUoBfpxQNluGRJp3b4otHdYZRan2RCDuDF32\nhcpGjFMOesz30VzEP/pw2wNPmmOXS/1NisF170Oosll1mhwG0swtluJqUZUt45LT\njpvR74cAZ3RBFvPllEtW3vGnJxgJWjhYUwTu1i23FW/E2bDogT9ik06S2rES56H0\nd+Hdy7+1sPir84q98nmx2h0BmbfWl7s1xHXLoEoBgQKBgQDzeTBrAeX6b6yPZgTt\nYEVl6cp3WMDSowB4utxuI/+lBAo2dBLzBr/UXfzqFWe5qVavu1Fx6bs2+Lx5z4yi\nNOCECChbmq2hXoTKCvIcXdEnY6JrL+d32t4h8tVOuLdxInL8NvPNcQpsoKLYhaF8\nx660rcEwz1WBXvjlTt/1L2EbyQKBgQDJO/W/G+m0MWQTBxzy4ZBWwq9hma9qGst7\nVtQBw8xokLbUqBL7nYczWGwKpdnYS9WYc4cTJ6v8FsC4k1aFrhzzYXjsQh5knwCc\n/pz2oQkR4z1wXL7gZo4cCQUih1zngh+ZChkJfvLSFJeTlVDcnWh3MwizmVIH7NQg\nxgPIENaAZwKBgGdVjSYtdRU4Zm2qJ/czf+DEPCkxIw2DHwUekcWxQ6QetdLsqso4\nmBwjE9+p3A8hfugwwV1ujQXExgGRBCgn9w4yhCZ03LJ7cjJqON2vN8DW+a0ydLQa\n0WJpNP0nSrwameDP1ePg0ULPXq408RgLi+ulPzRfGvRAgbSZKFZgmH95AoGBAIbX\nAKIgCAdQGSiO2Zz9/APGzFHv8xR8A+EPm1vbYTqnzXrNbHrhYVjMZQj1fPVsSyGu\nN9JkAOAYNub3A0DsHEYRCD/3RfpSeMy5519zJGqyA9corlYbIhozCRfL8DrIfHfF\nxmUQhZCzb6XapaZOa1OEBM6ja84XqUSUqrACaFj9AoGBAI5GJ1g9GLbG05NKIKdZ\nLRbmEuWBF05n5JrnumZva6rjA3Tp0yepm/s/HpTOkkPE/AzPwaEf3xnVjCXq3t50\noACJxM8TsBXMXVPdHJkx0LFlf59+k91+p7ELvERWBxDVKqAfoI6gxGXVKz5yjUia\nFpPaG5SgCl942MC2Ox7hUO+p\n-----END PRIVATE KEY-----\n","client_email":"sheet-accessord@lexical-script-460408-a5.iam.gserviceaccount.com","client_id":"105610417485295605792","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"https://www.googleapis.com/robot/v1/metadata/x509/sheet-accessord%40lexical-script-460408-a5.iam.gserviceaccount.com","universe_domain":"googleapis.com"})
if not SERVICE_ACCOUNT_JSON:
    raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON environment variable not set")
    
try:
    SERVICE_ACCOUNT_INFO = json.loads(SERVICE_ACCOUNT_JSON)
except json.JSONDecodeError as e:
    raise RuntimeError(f"Error parsing service account JSON: {str(e)}")

def get_sheet():
    """Get or create spreadsheet/worksheet"""
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
@app.route('/webhook', methods=['10000'])
def whatsapp_webhook():
    try:
        data = request.get_json()
        app.logger.info(f"Received webhook data")
        
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
