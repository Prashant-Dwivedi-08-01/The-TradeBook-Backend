import datetime
from flask import Blueprint
from flask import current_app as app
from utils.constants import ENTER_TRADE_ERROR, EXIT_TRADE_ERROR, FETCH_ALL_TRADES_ERROR
from utils.response import respond
from flask_restful import Api
from flask_jwt_extended import get_jwt_identity, jwt_required
from models.trade_model import Trade
from models.user_model import User
from flask import request

trade_api = Blueprint("trade_api", __name__)
trade_api_restful = Api(trade_api)

@trade_api.route("/enter_trade", methods = ["POST"])
@jwt_required()
def entr_trade():
    err_msg = None
    try:
        current_user = get_jwt_identity()
        user = User.objects(email=current_user["email"]).first()

        if not request.is_json:
            err_msg="Missing JSON in request"
            raise

        script = request.json.get("script", None)
        price = request.json.get("price", None)
        qty = request.json.get("qty", None)
        date = request.json.get("date", datetime.datetime.now())
        chart = request.json.get("chart", None)
        notes = request.json.get("notes", None)

        if not script:
            err_msg = "script is required"
            raise
        if not price:
            err_msg = "price is required"
            raise
        if not qty:
            err_msg = "qty is required"
            raise
        
        trade = Trade.objects(user=user, script=script).first()
        
        if not trade:
            entries = []
            entries.append((date, qty, price))
            total_qty = qty

            new_trade = Trade(user=user, script=script, entries=entries, total_qty = total_qty, status = "open")

            if chart:
                new_trade.chart_url = chart
            if notes:
                new_notes = []
                new_notes.append(notes)
                new_trade.notes = new_notes
            
            new_trade.save()
        else:
            # entry
            entries = trade.entries
            entries.append((date, qty, price))

            # total qty
            total_qty = trade.total_qty
            total_qty += int(qty)
            trade.total_qty = total_qty # as interger is immutable

            if chart and len(chart) != 0:
                trade.chart_url = chart
            if notes and len(notes) != 0:
                curr_notes = trade.notes
                curr_notes.append(notes)
            
            trade.save()

        res = {
            "msg": "Trade Information Saved Successfully",
        }

        app.logger.info("[%s] Trade Infromation Saved successfully.",user.email)

        return respond(data=res)

    except Exception as ex:
        app.logger.error("[%s] Error in inserting trade information. Error: %s.  Exception: %s", user.email, err_msg, str(ex))
        if not err_msg:
            err_msg = ENTER_TRADE_ERROR
        return respond(error=err_msg)

@trade_api.route("/exit_trade", methods=["POST"])
@jwt_required()
def exit_trade():
    err_msg = None
    try:
        current_user = get_jwt_identity()
        user = User.objects(email=current_user["email"]).first()

        if not request.is_json:
            err_msg="Missing JSON in request"
            raise

        script = request.json.get("script", None)
        price = request.json.get("price", None)
        qty = request.json.get("qty", None)
        date = request.json.get("date", datetime.datetime.now())
        chart = request.json.get("chart", None)
        notes = request.json.get("notes", None)
        
        if not script:
            err_msg = "script is required"
            raise
        if not price:
            err_msg = "price is required"
            raise
        if not qty:
            err_msg = "qty is required"
            raise

        trade = Trade.objects(user=user, script=script).first()
        if not trade:
            err_msg = "No entry was taken in this script"
            raise
        

        # qty
        curr_total_qty = trade.total_qty
        if curr_total_qty < int(qty):
            err_msg = "Insufficient shares to exit"
            raise
        curr_total_qty -= int(qty)
        trade.total_qty = curr_total_qty # as intergers are immutable

        # status
        if curr_total_qty == 0:
            trade.status = "close"

        # exits
        curr_exits = trade.exits
        curr_exits.append((date, qty, price))

        if chart:
            trade.chart_url = chart
        if notes:
            curr_notes = trade.notes
            curr_notes.append(notes)     

        trade.save()

        res = {
            "msg": "Exit Information Saved Successfully",
            "trade_info": trade.to_json()
        }

        app.logger.info("[%s] Exit Infromation Saved successfully.",user.email)

        return respond(data=res)

    except Exception as ex:
        app.logger.error("[%s] Error in exiting trade information. Error: %s.  Exception: %s", user.email, err_msg, str(ex))
        if not err_msg:
            err_msg = EXIT_TRADE_ERROR
        return respond(error=err_msg)


@trade_api.route("/all_trades", methods = ["GET"])
@jwt_required()
def all_trades():
    err_msg = None
    try:
        current_user = get_jwt_identity()
        user = User.objects(email=current_user["email"]).first()

        trades = Trade.objects(user=user)
        all_trade_info = []
        for trade in trades:
            all_trade_info.append(trade.to_json())
        
        res = {
            "msg": "Trades fetched successfully",
            "trades_info": all_trade_info
        }

        app.logger.info("[%s] All the trades fethched successfully", user.email)

        return respond(data=res)

    except Exception as ex:
        app.logger.error("[%s] Error in fetching all trades. Error: %s.  Exception: %s", user.email, err_msg, str(ex))
        if not err_msg:
            err_msg = FETCH_ALL_TRADES_ERROR
        return respond(error=err_msg)