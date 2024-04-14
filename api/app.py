from flask import Flask, render_template, request, redirect
import os

from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash


import time
from datetime import date, datetime, timedelta
from collections import defaultdict
import requests

import atexit
import json

import logging.config
import logging.handlers
import pathlib


class Blackbucks:
    def __init__(self, userToken):
        self.userToken = userToken
        self.headers = headers = {
            'accept': 'application/json, text/plain, */*',
            'authorization': f'Bearer {userToken}',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
        }
        print("Class instantiated !")

    def getTestDetails(self, hackathon_id=144):
        response = requests.get(f'https://taptap.blackbucks.me/api/hackathon/{hackathon_id}', headers=self.headers)
        return response.json()

    def getRoundDetails(self, rnd_id=369):

        response = requests.get(f'https://taptap.blackbucks.me/api/hackathon/round/{rnd_id}',  headers=self.headers)
        data  = response.json()
        return data
    
    def register(self, hackathon_id):
        response = requests.post(f'https://taptap.blackbucks.me/api/hackathon/registration/{hackathon_id}', headers=self.headers)
        return response.json()
    
    def create_participation(self, hackathon_id, round_id):
        response = requests.post(
            f'https://taptap.blackbucks.me/api/hackathon/create/participation/{hackathon_id}/{round_id}',
            headers=self.headers,
        )

        return response.json().get("attemptId")
    
    def end_hackathon(self, hackathon_id, round_id, attempt_id):
        params = {
            'hackathonId': hackathon_id,
            'roundId': round_id,
            'attemptId': attempt_id,
        }

        response = requests.put('https://taptap.blackbucks.me/api/hackathon/end', params=params, headers=self.headers)

        return response.json()

    def results(self, hackathon_id):
        res = requests.get(f"https://taptap.blackbucks.me/api/hackathon/overallScore/{hackathon_id}", headers=self.headers)
        data = res.json()
        test_name = data.get("testName")
        if test_name:
            score = f"{data.get('score')}/{data.get('totalScore')}"
            return True, score
        return False, "0/0"

    def submit_answer(self, qnsIndex, problemId, ans_list, hackathon_id, roundId, attemptId, sub_ans="", code=""):
        params = {
            'attemptId': attemptId,
            'createSubmission': 'true',
            'questionOrder': qnsIndex,
        }
        st_time = datetime.utcnow().isoformat(sep='T', timespec='milliseconds') + 'Z'
        end_time = datetime.now().strftime('%a %b %d %Y %H:%M:%S GMT+0530 (India Standard Time)')

        json_data = {
            'problemId': problemId,
            'language': 'python',
            'code': code,
            'roundId': roundId,
            'startTime': st_time,
            'endTime': end_time,
            'questionType': 'mcq' if ans_list else "subjective",
            'mcqAnswer': ans_list ,
            'subjectiveAnswer': sub_ans,
            'files': None,
            'recordingUrl': '',
            'isPractice': False,
        }

        response = requests.post(
            f'https://taptap.blackbucks.me/api/hackathon/testsubmission/{hackathon_id}',
            params=params,
            headers=self.headers,
            json=json_data,
        )

        if(response.json().get("isSuccess")):
            print(f"{qnsIndex+1} Done ✅")
            return True
        else:
            print(f"Problem with ProblemId {problemId} roundId {roundId} attemptId {attemptId} hackathon_id {hackathon_id}")
            return False

    def write_hackathon(self, hackathon_id, attemptId=None, endhack=False):
        print(f"Hackathon id {hackathon_id}")

        json_data = self.getTestDetails(hackathon_id)

        if(not json_data.get("isRegistered")):
            print("Registerd to the hackathon")
            self.register(hackathon_id)

        for rnd_no, rnd in enumerate(json_data["rounds"]):
            round_id = rnd.get("id")
            data = self.getRoundDetails(round_id)

            print(f"Round id {round_id}")

            startDate = date.fromisoformat(data.get("startDate"))
            endDate = date.fromisoformat(data.get("endDate"))

            eroju = date.today()
            if not (startDate<=eroju and eroju<=endDate):
                print("Round not Active")
                continue

            rounds_qns = defaultdict(int)

            for block in data["blocks"]:
                rounds_qns[block["problemType"]]+=block["points"]

            scored = 0
            total = 0
            for problem_type in rounds_qns:
                if problem_type == "mcq" or problem_type == "subjective":
                    scored += rounds_qns[problem_type]
                total+= rounds_qns[problem_type]

            if total==0:
                print("no rounds exits")
                continue

            percent = (scored / total)* 100
            print(f"Percentage is {percent}")

            if percent >= 40:
                print("Probability of getting marks is greater than 40, So writing")
            else:
                print(f"Probability of getting marks is less than 40, Write your Own {hackathon_id} {round_id}")
                continue

            if not attemptId:
                attemptId = self.create_participation(hackathon_id, round_id)
            
            print(f"Attempt id {attemptId}")


            for prob_no, problem in enumerate(data["blocks"]):
                print(f"Solving problem {prob_no}")
                try:
                    if problem["problemType"] == "mcq":
                        ans_list = []
                        for opt_no, option in enumerate(problem["mcq"]["options"]):
                            if option["isCorrectOption"]:
                                if option.get("id"):
                                    ans_list.append(option.get("id"))

                        self.submit_answer(prob_no, problem["id"], ans_list, hackathon_id, round_id, attemptId)
                        # time.sleep(1)

                    if problem["problemType"] == "subjective":
                        sub_answer = problem["subjective"].get("answer")
                        if sub_answer:
                            self.submit_answer(prob_no, problem["id"], [], hackathon_id, round_id, attemptId, sub_ans=sub_answer)


                    if problem["problemType"]=="coding":
                        print("Got Coding problem hackathon_id {hackathon_id} round_id {round_id} attemptId {attemptId}")
                        pass

                except Exception as e:
                    print(e)

            print("Edit the submission")
            print(f"https://taptap.blackbucks.me/editor/{round_id}/?hackathonid={hackathon_id}&isAdaptive=false&attemptId={attemptId}")
            if json_data["rounds"] and endhack:
                self.end_hackathon(hackathon_id, round_id, attemptId)
                self.results(hackathon_id)
                print("chek your results here ")
                print(f"https://taptap.blackbucks.me/hackathon/results/{hackathon_id}")

    def complete_lesson(self, fsd=False, aiml=False, write_all=False,  write_uncompleted=False):

        if fsd and not aiml:
            lessonPlan = 32
        elif aiml and not fsd:
            lessonPlan = 31
        else:
            print("Please specify domain correctly")
            return

        url = f'https://taptap.blackbucks.me/api/lessonPlan/student/{lessonPlan}'

        response = requests.get(url, headers=self.headers)

        ans = []
        for cnt, test in enumerate(response.json().get("list")):
            if test.get("type") == "link":
                lessonPhaseContentId = test.get("lessonPhaseContentId")
                if lessonPhaseContentId:
                    r = requests.post(f"https://taptap.blackbucks.me/api/lessonplan/{lessonPlan}/link/{lessonPhaseContentId}/recordLink", headers=self.headers)
                    print(r.json()["message"])

            if test.get("type") == "hackathon":
                title = test.get("lessonPhaseTitle")
                hackathon_id = test.get("lessonPhaseContentId")
                mcqCount = test.get("mcqCount")
                fileCount = test.get("fileCount")
                subjectiveCount = test.get("subjectiveCount")
                codingCount = test.get("codingCount")
                audioCount = test.get("audioCount")


                if write_all:
                    self.write_hackathon(hackathon_id, endhack=True)
                elif write_uncompleted:
                    status, _ = self.results(hackathon_id)
                    if not status:
                        self.write_hackathon(hackathon_id, endhack=True)

                _ , score = self.results(hackathon_id)

                ans.append((hackathon_id, title, score))
                
        
        return ans



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
    app.run(debug=True,host='0.0.0.0',port=port)