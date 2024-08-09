from flask import Flask
from routes.bingx import bingx as bingx_route

app = Flask(__name__)

app.register_blueprint(bingx_route)

@app.route('/')
def hello_world():
    return 'Hello, Zonix !'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)