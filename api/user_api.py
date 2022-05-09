
import re
from flask_restful import  Api
from flask import Blueprint
from models.user_model import User
from flask import request
from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from utils.constants import( 
    ACCOUNT_DELETE_ERROR, 
    FETCH_USERS_ERROR, 
    LOGOUT_ERROR, 
    USER_LOGIN_ERROR, 
    USER_REGISTRATION_ERROR,
    FORGET_PASSWORD_ERROR,
    RESET_PASSEORD_ERROR,
    EMAIL_REGEX)
from utils.response import set_response
from flask import current_app as app
from utils.common import delete_expired_jwt_tokens, revoke_jwt_token, mailer
from config.extensions import redis

user_api = Blueprint("user_api", __name__)
user_api_restful = Api(user_api)


@user_api.route("/", methods=["GET"])
def index():
    return set_response(data={
        "msg":"Welcome"
    })

@user_api.route("/register", methods=["POST"])
def register():
    err_msg = None
    try:
        if not request.is_json:
            err_msg="Missing JSON in request"
            raise
        first_name = request.json.get("first_name")
        last_name = request.json.get("last_name", "")
        email = request.json.get("email")
        phone = request.json.get("phone")
        password = request.json.get("password")

        if not first_name:
            err_msg = "first_name is required"
            raise

        if not email:
            err_msg = "email is required"
            raise

        if not re.fullmatch(EMAIL_REGEX, email):
            err_msg = "Invalid Email"
            raise

        if not phone:
            err_msg = "Phone is required"
            raise
        if not password:
            err_msg = "Password is required"
            raise

        user_exits = User.objects(email=email).first()
        if user_exits:
            err_msg = "This email is already registered"
            raise

        user = User(
            first_name = first_name,
            last_name = last_name,
            email = email,
            phone = phone
        )

        user.set_password(password)
        user.save()

        app.logger.info("[%s] Registered successfully", email)
        res = {
            "msg":"User registered successfully",
            "user_details": user.to_json()
        }
        return set_response(data=res)
    except Exception as ex:
        app.logger.error("[%s] Error in registering the user. Error: %s. Exception %s", email, err_msg, str(ex))
        if not err_msg:
            err_msg = USER_REGISTRATION_ERROR
        return set_response(error=err_msg)
    
    

@user_api.route("/login", methods=["POST"])
def login():
    err_msg = None
    try:
        if not request.is_json:
            err_msg="Missing JSON in request"
            raise
        email = request.json.get("email", None)
        password = request.json.get("password", None)

        if not email:
            err_msg = "email is required"
            raise
        if not password:
            err_msg = "password is required"
            raise

        user = User.objects(email=email).first()
        if not user:
            err_msg = "User not found"
            raise
        if not user.check_password(password):
            err_msg = "Incorrect Password"
            raise

        access_token = create_access_token(identity=user.to_json())

        app.logger.info("[%s] Logged in successfully", email)
        res = {
            "msg":"Login Successful",
            "access_token": access_token,
            "user_details": user.to_json()
        }
        return set_response(data=res)
    except Exception as ex:
        app.logger.error("[%s] Error in logging. Error: %s. Exception: %s", email, err_msg, str(ex))
        if not err_msg:
            err_msg = USER_LOGIN_ERROR
        return set_response(error=err_msg)
    
    

@user_api.route("/get_users", methods=["GET"])
@jwt_required()
def getUsers():
    err_msg = None
    try:
        current_user = get_jwt_identity()
        user = User.objects(email=current_user["email"]).first()
        users = User.objects()

        user_info = []
        for user in users:
            user_info.append(user.to_json())

        res = {
            "users": user_info
        }

        app.logger.info("[%s] All users information fetched successfully.",user.email)
        return set_response(data=res)
    except Exception as ex:
        app.logger.error("[%s] Error in fetching the users. Error: %s.  Exception: %s", user.email, err_msg, str(ex))
        if not err_msg:
            err_msg = FETCH_USERS_ERROR
        return set_response(error=err_msg)

@user_api.route("/delete_account", methods=["DELETE"])
@jwt_required()
def delete_account():
    err_msg = None
    try:
        current_user = get_jwt_identity()
        user = User.objects(email=current_user["email"]).first()

        password = request.json.get("password")
        if not password:
            err_msg = "Password is required"
            raise
        if not user.check_password(password):
            err_msg = "Bad Credentials"
            raise

        user.delete()

        revoke_jwt_token(user)

        app.logger.info("[%s] Account Deleted Successfully. All data removed", user.email)
        
        res = {
            "msg": "Account deleted successfully"
        }
        return set_response(data=res)
    except Exception as ex:
        app.logger.error("[%s] Error in deleting the account. Error: %s. Exception: %s", user.email, err_msg, str(ex))  
        if not err_msg:
            err_msg = ACCOUNT_DELETE_ERROR
        return set_response(error=err_msg)


@user_api.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    err_msg = None
    try:
        current_user = get_jwt_identity()
        user = User.objects(email = current_user['email']).first()

        revoke_jwt_token(user)

        delete_expired_jwt_tokens(user)

        app.logger.info("[%s] Logged Out Successfully", user.email)
        res = {
            "msg": "Logged Out Successfully"
        }

        return set_response(data=res)

    except Exception as ex:
        app.logger.error("[%s] Error in loggin out. Error: %s. Exception: %s", user.email, err_msg, str(ex))
        if not err_msg:
            err_msg = LOGOUT_ERROR
        return set_response(error=err_msg)


@user_api.route("/forget_password", methods=['POST'])
def forget_password():
    err_msg = None
    try:
        if not request.is_json:
            err_msg = "Please Provide Json Data"
            raise

        email = request.json.get("email", None)
        if not email:
            err_msg = "Registered Email is required"
            raise

        user = User.objects(email=email).first()

        if not user:
            err_msg = "This email is not registered"
            raise

        user_id = user.id

        key = f"forget_pass_{email}"
        val = "active"

        redis.set(key, val, ex=300) # expires after 5 min

        message = f"""
            Your Password Reset Request is recieved.

            Proceed to this link to reset your password http://127.0.0.1:5000/api/reset_password/{user_id}

            This Link will expire in 5 minutes.

            If not done by you then please considering reseting your password.
        """
        mailer(email, message)

        res = {
            "msg" : "Password Reset email sent successfully"
        }
        return set_response(data=res)
    except Exception as ex:
        app.logger.error("[%s] Error in Forget Password. Error: %s. Exception: %s", email, err_msg, str(ex))
        if not err_msg:
            err_msg = FORGET_PASSWORD_ERROR
            raise
        return set_response(error=err_msg)


@user_api.route("/reset_password", methods=['POST'])
@user_api.route("/reset_password/<user_id>", methods=['GET'])
def reset_password(user_id = None):
    err_msg = None
    try:
        if request.method == "GET":

            user = User.objects(id=user_id).first()
            if not user:
                err_msg = "Invalid reset link"
                raise
            
            key = f"forget_pass_{user.email}"
            expiry_status = redis.get(key)

            if expiry_status == None:
                err_msg = "Either reset period has expired or your not eligible to reset the password. Please make a fresh request"
                raise

            res = {
                "email": user.email
            }
            return set_response(data = res)

        else:
            new_password = request.json.get("new_password", None)
            if not new_password:
                err_msg = "New Password is required"
                raise
            
            email = request.json.get("email", None)
            if not new_password:
                err_msg = "Email Is required"
                raise

            user = User.objects(email=email).first()
            if not user:
                err_msg = "This email is not registered"
                raise

            key = f"forget_pass_{email}"
            expiry_status = redis.get(key)

            if expiry_status == None:
                err_msg = "Either reset period expired or your not eligible to reset the password. Please make a fresh request"
                raise

            user.set_password(new_password)
            user.save()

            redis.delete(key)

            res = {
                "msg" : "Password rest successfull"
            }

            return set_response(data=res)

    except Exception as ex:
        app.logger.error("Error in resetting the password. Error: %s. Exception: %s", err_msg, str(ex))
        if not err_msg:
            err_msg = RESET_PASSEORD_ERROR
        return set_response(error=err_msg)