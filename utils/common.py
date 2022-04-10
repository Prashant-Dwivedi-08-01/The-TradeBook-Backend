import datetime
from flask_jwt_extended import get_jwt
from models.jwt_blocklist_model import TokenBlocklist
from flask import current_app as app

def revoke_jwt_token():
    try:
            
        jti = get_jwt()["jti"]
        expiry_timestap = get_jwt()["exp"]
        expiry = datetime.datetime.fromtimestamp(expiry_timestap)

        blocked_token = TokenBlocklist(jti=jti, expiry=expiry)

        blocked_token.save()
    except Exception as ex:
        app.logger.error("Error in revoking the JWT token")
        raise
