import datetime
from flask_jwt_extended import get_jwt
from models.jwt_blocklist_model import TokenBlocklist
from flask import current_app as app
import datetime

def revoke_jwt_token(user):
    try:
            
        jti = get_jwt()["jti"]
        expiry_timestap = get_jwt()["exp"]
        expiry = datetime.datetime.fromtimestamp(expiry_timestap)

        blocked_token = TokenBlocklist(jti=jti, expiry=expiry)

        blocked_token.save()
    except Exception as ex:
        app.logger.error("[%s] Error in revoking the JWT token. Exception: %s", user.email, str(ex))
        raise

def delete_expired_jwt_tokens(user):
    try:
        all_revoked_token = TokenBlocklist.objects()
        for token in all_revoked_token:
            expiry = token.expiry
            if expiry <= datetime.datetime.now():
                token.delete()

    except Exception as ex:
        app.logger.error("[%s] Error in deleting the expired JWT token. Exception: %s", user.email, str(ex))
        
        # no need to raise the exception as this has to be done as an extra fucntionality to present 
        # logout api call