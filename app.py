from flask import Flask, request
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import os

app = Flask(__name__)

# === Load Google Sheets credentials ===
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
client = gspread.authorize(creds)
sheet = client.open("OrdersSheet").sheet  # Change this to your sheet name

# === WhatsApp Webhook Verification ===
VERIFY_TOKEN = "my_verify_token_123"  # You can set this to anything, remember it!

@app.route('/')
def home():
    return 'WhatsApp Order Bot Running'

@app.route('/callback', methods=['GET', 'POST'])
def callback():
    if request.method == 'GET':
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return "Verification token mismatch", 403

    elif request.method == 'POST':
        data = request.get_json()
        try:
            for entry in data['entry']:
                for change in entry['changes']:
                    value = change['value']
                    messages = value.get('messages')
                    if messages:
                        for msg in messages:
                            phone = msg['from']
                            text = msg['text']['body']
                            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            sheet.append_row([phone, text, timestamp])
            return "Message processed", 200
        except Exception as e:
            print("Error:", e)
            return "Error", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
