from flask_mongoengine import MongoEngine
from flask_jwt_extended import JWTManager

# JWT
jwt = JWTManager()

# Database
db = MongoEngine()
