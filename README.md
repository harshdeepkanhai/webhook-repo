# Mongo Webhook

A flask application to capture webhook from github when pushed, pull_requested or merged to [actio-repo](https://github.com/harshdeepkanhai/action-repo)

## Steps
------------
* clone this repo
* Install python, ngrok and install flask, pymongo via pip
* `cd` into webhook-repo
* if you are in windows cmd type
`
set FLASK_APP=main.py
`
* setup your DB locally or on MongoDB Atlas
* Copy the url of your server(from:Atlas) or localurl(of mongo local installation) inside MongoClient and replace the url(although I have provided my Mongo URL for testing)
* run `flask run`
* run  `ngrok http 5000` it will generate a tunnel to your localhost. Copy the URL and paste it in your github repo after appending`/webhook` to the URL settings location (action-repo>settings>webhook).
* Use the URL with `/home` endpoint to see the UI, where all the pull request, pushes and merge have been done 