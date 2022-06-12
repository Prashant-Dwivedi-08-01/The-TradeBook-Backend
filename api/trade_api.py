import datetime
from flask import Blueprint
from flask import current_app as app
from utils.constants import ENTER_TRADE_ERROR, EXIT_TRADE_ERROR, FETCH_ALL_TRADES_ERROR, FETCH_TRADE_ERROR
from utils.response import respond
from flask_restful import Api
from flask_jwt_extended import get_jwt_identity, jwt_required
from models.trade_model import Trade
from models.user_model import User
from flask import request
from datetime import date


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
        
        today = date.today()

        script = request.json.get("script", None)
        price = request.json.get("price", None)
        qty = request.json.get("qty", None)
        trade_date = request.json.get("date", today.strftime("%b %d, %Y"))
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
            entries.append((trade_date, qty, price))
            total_qty = qty

            new_trade = Trade(user=user, script=script, entries=entries, total_qty = total_qty, status = "open")

            if chart:
                new_trade.chart_url = chart
            if notes:
                new_note = f'[Buy @{price}] {notes}'
                new_notes = []
                new_notes.append(new_note)
                new_trade.notes = new_notes
            
            total_money_invest_this_entry = int(qty)*float(price)
            new_trade.total_money_invest = total_money_invest_this_entry
            
            new_trade.save()
        else:
            # entry
            entries = trade.entries
            entries.append((trade_date, qty, price))

            # total qty
            total_qty = trade.total_qty
            total_qty += int(qty)
            trade.total_qty = total_qty # as interger is immutable

            if chart and len(chart) != 0:
                trade.chart_url = chart
            if notes and len(notes) != 0:
                new_note = f'[Buy @{price}] {notes}'
                curr_notes = trade.notes
                curr_notes.append(new_note)
            
            current_total_money_invest = trade.total_money_invest
            new_money_invest = current_total_money_invest + int(qty)*float(price)

            trade.total_money_invest = new_money_invest


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

        today = date.today()
        
        script = request.json.get("script", None)
        price = request.json.get("price", None)
        qty = request.json.get("qty", None)
        trade_date = request.json.get("date", today.strftime("%b %d, %Y"))
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
        curr_exits.append((trade_date, qty, price))

        if chart:
            trade.chart_url = chart
        if notes:
            new_note = f'[Sell @{price}] {notes}'
            curr_notes = trade.notes
            curr_notes.append(new_note)  

        current_total_money_exit = trade.total_money_exit
        new_total_money_exit = current_total_money_exit + int(qty)*float(price)  

        trade.total_money_exit = new_total_money_exit 

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


@trade_api.route("/trade/<script>", methods = ["GET"])
@jwt_required()
def trade_info(script):
    err_msg = None
    try:
        current_user = get_jwt_identity()
        user = User.objects(email=current_user["email"]).first()

        trade = Trade.objects(user=user, script=script).first()
        if not trade:
            err_msg = "No trade data exists for this Script"
            raise
        
        res = {
            "msg": "Trades fetched successfully",
            "trades_info": trade
        }

        app.logger.info("[%s] Trade Data Fetched Successfully ", user.email)

        return respond(data=res)

    except Exception as ex:
        app.logger.error("[%s] Error in fetching trade data. Error: %s.  Exception: %s", user.email, err_msg, str(ex))
        if not err_msg:
            err_msg = FETCH_TRADE_ERROR
        return respond(error=err_msg)