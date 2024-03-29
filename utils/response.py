from flask import jsonify

def respond(data=None, error=None):
    if error:
        success = False
    else:
        success = True
    res = {
        "data": data,
        "error": error,
        "success": success
    }
    return jsonify(res)