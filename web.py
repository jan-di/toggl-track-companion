from flask import Flask, request
import hashlib
import hmac
from util import load_config

app = Flask(__name__)
config = load_config()


@app.route("/")
def hello_world():

    args = request.args

    key_hash = hashlib.sha256(str.encode(config["TELEGRAM_TOKEN"])).hexdigest()

    cmp_hash = hmac.new(
        str.encode(key_hash), str.encode(""), hashlib.sha256
    ).hexdigest()

    # secret_key = SHA256(<bot_token>)
    # if (hex(HMAC_SHA256(data_check_string, secret_key)) == hash) {
    # // data is from Telegram
    # }

    return f"<p>Hello, World! {args.to_dict()}</p>key_hash:{key_hash}<br/>hash: {args.hash}<br/>cmp_hash:{cmp_hash}"


if __name__ == "__main__":
    app.run(debug=True, ssl_context="adhoc")
