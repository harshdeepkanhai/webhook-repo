from flask import json,render_template, request, Flask
import flask
from pymongo import MongoClient
client = MongoClient()
client = MongoClient('mongodb+srv://admin:admin@kanhai-cluster.fio7e.mongodb.net/myFirstDatabase?retryWrites=true&w=majority')
db = client.github
githook = db.githook
enum = ["PUSH","PULL_REQUEST","MERGE"]
app = Flask(__name__)

@app.route('/')
def api_root():
    return 'Welcome guys'

@app.route('/home')
def home():
   
    github = githook.find({})
    return render_template('index.html', github=github)

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