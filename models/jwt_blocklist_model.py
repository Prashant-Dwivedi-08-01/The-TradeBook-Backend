import datetime
from config.extensions import db

class TokenBlocklist(db.Document):
    jti = db.StringField(max_length = 36)
    expiry = db.DateTimeField()
    revoked_at = db.DateTimeField(default=datetime.datetime.now())