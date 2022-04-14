from datetime import timedelta
from flask import Flask
from config.extensions import db
from config.extensions import jwt
from flask import Flask
from api import user_api
from logging.config import dictConfig
from flask_cors import CORS
from models.jwt_blocklist_model import TokenBlocklist
from dotenv import load_dotenv
import os
load_dotenv()


def register_extension(app):
    jwt.init_app(app)
    db.init_app(app)


def set_logger():
    dictConfig({
        'version': 1,
        'formatters': {'default': {
            'format': '[%(asctime)s] [%(levelname)s] in [%(module)s]: %(message)s',
        }},
        'handlers': {'wsgi': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://flask.logging.wsgi_errors_stream',
            'formatter': 'default'
        }},
        'root': {
            'level': 'INFO',
            'handlers': ['wsgi']
        }
    })


def set_jwt_token():
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload["jti"]
        token = TokenBlocklist.objects(jti = jti).first()
        return token is not None

def set_app_blueprints(app):
    app.register_blueprint(user_api.user_api, url_prefix = "/api")


def create_app():
    app = Flask(__name__)
    CORS(app)
    app.config['MONGODB_SETTINGS'] = {
        'host': os.getenv("DATABASE_HOST"),
    }
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=2)

    register_extension(app)
    set_app_blueprints(app)
    set_logger()
    set_jwt_token()

    return app

app = create_app()

# We are using gunicorn
# if __name__ == "__main__":
#     app.run(debug=True)