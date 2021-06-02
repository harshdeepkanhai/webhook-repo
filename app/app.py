from app.webhook import routes
from flask import Flask
from app.webhook.routes import webhook, ui
def create_app():
    app = Flask(__name__)
    app.register_blueprint(webhook)
    app.register_blueprint(ui)
    
    @app.route('/')
    def index():
        return 'Welcome guys Use the /home endpoint to see the repo activity'
    
    return app