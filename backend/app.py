from flask import Flask, request

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST', 'PUT', 'DELETE'])
def index():
    return f"Hello! The backend received a {request.method} request.\n"

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    return "FLAG{HRS_Bypass_Successful} - Welcome Admin!\n"