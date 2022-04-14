from datetime import timedelta
from flask import Flask
from config.extensions import db
from config.extensions import jwt
from flask import Flask
from api import user_api
from logging.config import dictConfig
import logging
from flask_cors import CORS
from models.jwt_blocklist_model import TokenBlocklist
from dotenv import load_dotenv
import os
load_dotenv()


app = Flask(__name__)
CORS(app)
app.config['MONGODB_SETTINGS'] = {
    'host': os.getenv("DATABASE_HOST"),
}
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=2)


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

logger_blocklist = [
    "_internal",
]

for module in logger_blocklist:
    logging.getLogger(module).setLevel(logging.ERROR)

jwt.init_app(app)
db.init_app(app)

@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    token = TokenBlocklist.objects(jti = jti).first()
    return token is not None

app.register_blueprint(user_api.user_api, url_prefix = "/api")

if __name__ == "__main__":
    app.run(debug=True)