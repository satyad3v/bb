from flask import Flask, render_template, request, redirect
import os

from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from bbapi import Blackbucks

app = Flask(__name__)
port = int(os.environ.get("PORT", 5000))
DEBUG = bool(os.environ.get("DEBUG", True))

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
        userToken = request.form['userToken']
        internType = request.form['internType']
        print(userToken, internType)
        bb = Blackbucks(userToken)

        if request.form.get('write_all'):
            write_all = True
        else:
            write_all = False
        
        if request.form.get('write_uncompleted'):
            write_uncompleted = True
        else:
            write_uncompleted = False

        if internType == "AIML":
            result = bb.complete_lesson(aiml=True, write_uncompleted=write_uncompleted, write_all=write_all)
        else:
            result = bb.complete_lesson(fsd=True, write_all=write_all, write_uncompleted=write_uncompleted)


        return render_template("lister.html", result = result, token = userToken)
    
    return render_template('home.html')

@app.route('/rewrite',  methods=['GET'])
@auth.login_required
def rewrite():

    userToken = request.args.get("userToken")
    hid = request.args.get("hid")
    print(userToken, hid)
    bb = Blackbucks(userToken)

    result = bb.write_hackathon(hid, endhack=True)

    return redirect(f"https://taptap.blackbucks.me/hackathon/results/{hid}")






if __name__ == '__main__':
    app.run(debug=DEBUG,host='0.0.0.0',port=port)