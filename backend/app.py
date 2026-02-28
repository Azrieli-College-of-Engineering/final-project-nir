from flask import Flask, request

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST', 'PUT', 'DELETE'])
def index():
    return f"Hello! The backend received a {request.method} request.\n"