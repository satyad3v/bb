import time
from datetime import date, datetime, timedelta
from collections import defaultdict
import requests

import atexit
import json

import logging.config
import logging.handlers
import pathlib


logger = logging.getLogger("my_app")

def setup_logging():
    config_file = pathlib.Path("logging_config.json")
    with open(config_file) as f_in:
        config = json.load(f_in)

    logging.config.dictConfig(config)

setup_logging()
logging.basicConfig(level="INFO")

class Blackbucks:
    def __init__(self, userToken):
        self.userToken = userToken
        self.headers = headers = {
            'accept': 'application/json, text/plain, */*',
            'authorization': f'Bearer {userToken}',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
        }
        logger.info("Class instantiated !")

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
        return False, 0

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
            logger.info(f"{qnsIndex+1} Done ✅")
            return True
        else:
            logger.error(f"Problem with ProblemId {problemId} roundId {roundId} attemptId {attemptId} hackathon_id {hackathon_id}")
            return False

    def write_hackathon(self, hackathon_id, attemptId=None, endhack=False):
        logger.debug(f"Hackathon id {hackathon_id}")

        json_data = self.getTestDetails(hackathon_id)

        if(not json_data.get("isRegistered")):
            logger.info("Registerd to the hackathon")
            self.register(hackathon_id)

        for rnd_no, rnd in enumerate(json_data["rounds"]):
            round_id = rnd.get("id")
            data = self.getRoundDetails(round_id)

            logger.debug(f"Round id {round_id}")

            startDate = date.fromisoformat(data.get("startDate"))
            endDate = date.fromisoformat(data.get("endDate"))

            eroju = date.today()
            if not (startDate<=eroju and eroju<=endDate):
                logger.info("Round not Active")
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
                logger.info("no rounds exits")
                continue

            percent = (scored / total)* 100
            logger.info(f"Percentage is {percent}")

            if percent >= 70:
                logger.info("Probability of getting marks is greater than 70, So writing")
            else:
                logger.info(f"Probability of getting marks is less than 70, Write your Own {hackathon_id} {round_id}")
                continue

            if not attemptId:
                attemptId = self.create_participation(hackathon_id, round_id)
            
            logger.debug(f"Attempt id {attemptId}")


            for prob_no, problem in enumerate(data["blocks"]):
                logger.info(f"Solving problem {prob_no}")
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
                        logger.warning("Got Coding problem hackathon_id {hackathon_id} round_id {round_id} attemptId {attemptId}")
                        pass

                except Exception as e:
                    print(e)

            logger.info("Edit the submission")
            logger.debug(f"https://taptap.blackbucks.me/editor/{round_id}/?hackathonid={hackathon_id}&isAdaptive=false&attemptId={attemptId}")
            if json_data["rounds"] and endhack:
                self.end_hackathon(hackathon_id, round_id, attemptId)
                self.results(hackathon_id)
                logger.info("chek your results here ")
                logger.debug(f"https://taptap.blackbucks.me/hackathon/results/{hackathon_id}")

    def complete_lesson(self, fsd=False, aiml=False, write=False):

        if fsd and not aiml:
            lessonPlan = 32
        elif aiml and not fsd:
            lessonPlan = 31
        else:
            logger.error("Please specify domain correctly")
            return

        url = f'https://taptap.blackbucks.me/api/lessonPlan/student/{lessonPlan}'

        response = requests.get(url, headers=self.headers)

        ans = []
        for cnt, test in enumerate(response.json().get("list")):
            if test.get("type") == "link":
                lessonPhaseContentId = test.get("lessonPhaseContentId")
                if lessonPhaseContentId:
                    r = requests.post(f"https://taptap.blackbucks.me/api/lessonplan/{lessonPlan}/link/{lessonPhaseContentId}/recordLink", headers=self.headers)
                    logger.info(r.json()["message"])

            if test.get("type") == "hackathon":
                title = test.get("lessonPhaseTitle")
                hackathon_id = test.get("lessonPhaseContentId")
                mcqCount = test.get("mcqCount")
                fileCount = test.get("fileCount")
                subjectiveCount = test.get("subjectiveCount")
                codingCount = test.get("codingCount")
                audioCount = test.get("audioCount")

                if write:
                    self.write_hackathon(hackathon_id, endhack=True)

                completed, score = self.results(hackathon_id)
                test_link = f"https://taptap.blackbucks.me/hackathon/allRounds/{hackathon_id}/"

                if completed:
                    score_link = f"https://taptap.blackbucks.me/hackathon/results/{hackathon_id}"
                    ans.append((hackathon_id, title, score))
        
        return ans
