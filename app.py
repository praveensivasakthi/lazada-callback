from flask import Flask, request

app = Flask(__name__)

@app.route('/')
def home():
    return 'Lazada callback server is live!'

@app.route('/callback')
def callback():
    code = request.args.get('code')
    return f'Authorization code received: {code}', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
