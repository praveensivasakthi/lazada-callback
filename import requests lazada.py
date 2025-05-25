from flask import Flask, request

app = Flask(__name__)

@app.route('/', methods=['GET'])
def receive_code():
    code = request.args.get('code')
    return f"Lazada sent this code: {code}", 200

if __name__ == '__main__':
    app.run()
