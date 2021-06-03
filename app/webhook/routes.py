from flask import Blueprint, request, render_template, jsonify
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
    return render_template('index.html')

@ui.route('/get_git_data')
def get_git_data():
    githook.delete_many({"timestamp": { "$lte": dt.now() - timedelta(seconds=100)}})
    github_data = githook.find({"timestamp": { "$gte": dt.now() - timedelta(seconds=1000000)}}).sort([("timestamp",-1),])
    github_actions_list = []
    for activity in github_data:
        if activity.action == "PUSH":
            github_actions_list.append(f'<li class="git-activity"><span class="type-0">PUSH: </span><span> <span class="author">{activity.author }</span> pushed to <span class="to">{activity.to_branch}</span> on <span class="datetime">{ custom_strftime("{S} %B %Y - %I:%M %p %Z",activity.timestamp) } UTC</span></li>')
        elif activity.action == "PULL_REQUEST":
            github_actions_list.append(f'<li class="git-activity"><span class="type-1">PULL_REQUEST: </span><span class="author">{ activity.author }</span> submitted a pull request from <span class="from">{ activity.from_branch }</span> to <span class="to">{ activity.to_branch}</span> on <span class="datetime">{ custom_strftime("{S} %B %Y - %I:%M %p %Z",activity.timestamp) } UTC</span></li>')
        elif activity.action == "MERGE":
            github_actions_list.append(f'<li class="git-activity"><span class="type-2">MERGE: </span><span><span class="author">{activity.author }</span> merged branch from <span class="from">{ activity.from_branch }</span> to <span class="to">{ activity.to_branch}</span> on <span class="datetime">{ custom_strftime("{S} %B %Y - %I:%M %p %Z",activity.timestamp) } UTC</span></li>')

    return github_data

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
    return status_code