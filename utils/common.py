import datetime
from flask_jwt_extended import get_jwt
from models.jwt_blocklist_model import TokenBlocklist
from flask import current_app as app
import os
from dotenv import load_dotenv
load_dotenv()

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

def mailer(email, msg):
    try:
        import smtplib, ssl
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart



        port = 465
        smtp_server = "smtp.gmail.com"
        sender_email = "194princedubey@gmail.com"
        password = os.getenv("EMAIL_PASSWORD")
        
        receiver_email = email

        message = MIMEMultipart("alternative")
        message["Subject"] = "Trade Book Password Reset"
        message["From"] = sender_email
        message["To"] = receiver_email

        temp = MIMEText(msg, "plain")

        message.attach(temp)

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        
        app.logger.info("[%s] Email sent for password reset.", email)
    except Exception as ex:
        app.logger.error("[%s] Error in sending the email. Exception: %s", email, str(ex))
        raise