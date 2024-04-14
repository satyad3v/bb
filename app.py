from flask import Flask, render_template, request, redirect
import os

from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
import requests

app = Flask(__name__)
port = int(os.environ.get("PORT", 5000))

auth = HTTPBasicAuth()

users = {
    "charan" : generate_password_hash("charan"),
    "raju" : generate_password_hash("raju"),
    "admin": generate_password_hash("iamNagasatya"),
}


@auth.verify_password
def verify_password(username, password):
    if username in users and \
            check_password_hash(users.get(username), password):
        return username


@app.route('/',  methods=['POST', 'GET'])
@auth.login_required
def home():
    if request.method == 'POST':
        # userToken = request.form['token']
        userToken = request.form['userToken']
        print(userToken)
        # internType = 
        return render_template("lister.html", data = data)
    
    return render_template('home.html')




if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0',port=port)