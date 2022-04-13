
from flask_restful import  Api
from flask import Blueprint
from models.user_model import User
from flask import request
from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from utils.constants import ACCOUNT_DELETE_ERROR, FETCH_USERS_ERROR, LOGOUT_ERROR, USER_LOGIN_ERROR, USER_REGISTRATION_ERROR
from utils.response import set_response
from flask import current_app as app
from utils.common import revoke_jwt_token

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

        app.logger.info("%s Registered successfully", email)
        res = {
            "msg":"User registered successfully",
            "user_details": user.to_json()
        }
        return set_response(data=res)
    except Exception as ex:
        app.logger.error("%s Error in registering the user. Error: %s. Exception %s", email, err_msg, str(ex))
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

        app.logger.info("%s Logged in successfully", email)
        res = {
            "msg":"Login Successful",
            "access_token": access_token
        }
        return set_response(data=res)
    except Exception as ex:
        app.logger.error("%s Error in logging. Error: %s. Exception: %s", email, err_msg, str(ex))
        if not err_msg:
            err_msg = USER_LOGIN_ERROR
        return set_response(error=err_msg)
    
    

@user_api.route("/get_users", methods=["POST"])
@jwt_required()
def getUsers():
    err_msg = None
    try:
        current_user = get_jwt_identity()
        user = User.objects(email=current_user["email"]).first()
        users = User.objects()
        res = {
            "users": users
        }

        app.logger.info("%s All users information fetched successfully.",user.email)
        return set_response(data=res)
    except Exception as ex:
        app.logger.error("%s Error in fetching the users. Error: %s.  Exception: %s", user.email, err_msg, str(ex))
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

        revoke_jwt_token()

        app.logger.info("%s Account Deleted Successfully.", user.email)
        
        res = {
            "msg": "Account deleted successfully"
        }
        return set_response(data=res)
    except Exception as ex:
        app.logger.error("%s Error in deleting the account. Error: %s. Exception: %s", user.email, err_msg, str(ex))  
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

        revoke_jwt_token()

        app.logger.info("%s Logged Out Successfully", user.email)
        res = {
            "msg": "Logged Out Successfully"
        }

        return set_response(data=res)

    except Exception as ex:
        app.logger.error("%s Error in loggin out. Error: %s. Exception: %s", user.email, err_msg, str(ex))
        if not err_msg:
            err_msg = LOGOUT_ERROR
        return set_response(error=err_msg)

