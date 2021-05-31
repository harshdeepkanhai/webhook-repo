from flask import json,render_template, request, Flask
import flask
from pymongo import MongoClient
from dateutil.parser import parse
from datetime import datetime as dt

client = MongoClient('mongodb+srv://admin:admin@kanhai-cluster.fio7e.mongodb.net/myFirstDatabase?retryWrites=true&w=majority')
db = client.github
githook = db.githook
enum = ["PUSH","PULL_REQUEST","MERGE"]
app = Flask(__name__)

def suffix(d):
    return 'th' if 11<=d<=13 else {1:'st',2:'nd',3:'rd'}.get(d%10, 'th')

def custom_strftime(format, t):
    return t.strftime(format).replace('{S}', str(t.day) + suffix(t.day))

@app.route('/')
def api_root():
    return 'Welcome guys Use the /home endpoint to see the repo activity'

@app.route('/home')
def home():
    github = githook.find()
    print(github)
    return render_template('index.html', github=github, custom_strftime=custom_strftime, fromisoformat=dt.fromisoformat, parse=parse)

@app.route('/webhook', methods=['POST'])
def api_webhook():
    data = {}
    if request.headers['Content-Type'] == 'application/json':
        github_request = request.get_json()
        githook = db.githook
        print(type(github_request))
        if "action" in github_request:
            if github_request["action"] == 'opened':
                data = {
                    "request_id": github_request["number"],
                    "author": github_request["pull_request"]["head"]["label"].split(':')[0],
                    "action": enum[1],
                    "from_branch": github_request["pull_request"]["head"]["label"],
                    "to_branch": github_request["pull_request"]["base"]["label"],
                    "timestamp": github_request["pull_request"]["created_at"]
                }
           
            elif github_request["action"] == 'closed' and github_request["pull_request"]["merged"] == True:
                data = {
                    "request_id": github_request["pull_request"]["merge_commit_sha"],
                    "author": github_request["pull_request"]["merged_by"]["login"],
                    "action": enum[2],
                    "from_branch": github_request["pull_request"]["head"]["label"],
                    "to_branch": github_request["pull_request"]["base"]["label"],
                    "timestamp": github_request["pull_request"]["updated_at"]
                }
                print(data)
        elif "after" in github_request and githook.find({"request_id":github_request["after"] }).count() == 0:
            data = {
                    "request_id": github_request["after"],
                    "author": github_request["pusher"]["name"],
                    "action": enum[0],
                    "from_branch": f"{ github_request['sender']['html_url'].split('/')[-1]}:{github_request['ref'].split('/')[-1]}",
                    'to_branch': f"{ github_request['sender']['html_url'].split('/')[-1]}:{github_request['ref'].split('/')[-1]}",
                    "timestamp": github_request["head_commit"]["timestamp"]
                }
    githook.insert_one(data)
    status_code = flask.Response(status=201)
    return status_code

if __name__ == '__main__':
    app.run(debug=True)