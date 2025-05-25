from flask import Flask, request

app = Flask(__name__)

@app.route('/')
def home():
    return 'Lazada Callback App Running'

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if code:
        return f'Authorization Code received: {code}'
    else:
        return 'No authorization code received', 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
