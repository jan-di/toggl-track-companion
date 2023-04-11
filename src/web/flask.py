from flask import Flask


class FlaskApp:
    def __init__(self, server_name: str, session_secret: str):
        self.app = Flask(__name__)
        self.app.config.update(SERVER_NAME=server_name, SECRET_KEY=session_secret)

    def run(self):
        self.app.run(
            debug=True, ssl_context="adhoc", use_reloader=False, host="0.0.0.0"
        )


# @app.route("/auth")
# def auth():
#     auth_valid = telegram.validate_web_auth(
#         config.telegram_token, request.args.to_dict()
#     )
#     if auth_valid:
#         session["user_id"] = request.args["id"]
#     else:
#         return "authentication invalid", 401

#     return redirect(request.args["_next"], code=302)
