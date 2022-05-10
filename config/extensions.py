from flask_mongoengine import MongoEngine
from flask_jwt_extended import JWTManager
import redis
import os
from dotenv import load_dotenv
load_dotenv()

# JWT
jwt = JWTManager()

# Database
db = MongoEngine()

redis = redis.Redis(
    host=os.getenv("TRADEBOOK_REDIS_HOST"),
    port=os.getenv("TRADEBOOK_REDIS_PORT"), 
    password=os.getenv("TRADEBOOK_REDIS_PASSWORD")
)