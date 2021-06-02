from flask import Blueprint, request, render_template
import flask
from app.extensions import githook
from dateutil.parser import parse
from dateutil.tz import UTC
from datetime import datetime as dt
from datetime import timedelta

enum_github_event = ["PUSH","PULL_REQUEST","MERGE"]

def suffix(d):
    return 'th' if 11<=d<=13 else {1:'st',2:'nd',3:'rd'}.get(d%10, 'th')

def custom_strftime(format, t):
    return t.strftime(format).replace('{S}', str(t.day) + suffix(t.day))

webhook = Blueprint('Webhook', __name__, url_prefix='/webhook')
ui = Blueprint('Home', __name__, url_prefix='')


@ui.route('/home')
def home():
    githook.delete_many({"timestamp": { "$lte": dt.now() - timedelta(seconds=100)}})
    github = githook.find({"timestamp": { "$gte": dt.now() - timedelta(seconds=1000000)}}).sort([("timestamp",-1),])
    return render_template('index.html', github=github, custom_strftime=custom_strftime, parse=parse)

@webhook.route('/receiver', methods=["POST"])
def api_webhook():
    mongo_push_data = {}
    if request.headers['Content-Type'] == 'application/json':
        github_request = request.get_json()
        if "action" in github_request:
            if github_request["action"] == 'opened':
                mongo_push_data = {
                    "request_id": github_request["number"],
                    "author": github_request["pull_request"]["head"]["label"].split(':')[0],
                    "action": enum_github_event[1],
                    "from_branch": github_request["pull_request"]["head"]["label"],
                    "to_branch": github_request["pull_request"]["base"]["label"],
                    "timestamp": parse(github_request["pull_request"]["created_at"]).astimezone(UTC)
                }
           
            elif github_request["action"] == 'closed' and github_request["pull_request"]["merged"] == True:
                mongo_push_data = {
                    "request_id": github_request["pull_request"]["merge_commit_sha"],
                    "author": github_request["pull_request"]["merged_by"]["login"],
                    "action": enum_github_event[2],
                    "from_branch": github_request["pull_request"]["head"]["label"],
                    "to_branch": github_request["pull_request"]["base"]["label"],
                    "timestamp": parse(github_request["pull_request"]["updated_at"]).astimezone(UTC)
                }
        elif "after" in github_request and githook.find({"request_id":github_request["after"] }).count() == 0:
            mongo_push_data = {
                    "request_id": github_request["after"],
                    "author": github_request["pusher"]["name"],
                    "action": enum_github_event[0],
                    "from_branch": f"{ github_request['sender']['html_url'].split('/')[-1]}:{github_request['ref'].split('/')[-1]}",
                    'to_branch': f"{ github_request['sender']['html_url'].split('/')[-1]}:{github_request['ref'].split('/')[-1]}",
                    "timestamp": parse(github_request["head_commit"]["timestamp"]).astimezone(UTC)
                }
    githook.insert_one(mongo_push_data)
    status_code = flask.Response(status=201)
    github = githook.find({"timestamp": { "$gte": dt.now() - timedelta(seconds=1000000)}}).sort([("timestamp",-1),])
    return render_template('index.html', github=github, custom_strftime=custom_strftime, parse=parse), status_code