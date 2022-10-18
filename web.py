from flask import Flask, request
import hashlib
import hmac
from util import load_config

app = Flask(__name__)
config = load_config()


def validate_telegram_auth(token: str, params: dict[str]):
    token_hash = hashlib.sha256(str.encode(token)).digest()
    check_hash = params["hash"]

    params = params.copy()
    params.pop("hash")

    compare_string = "\n".join(map(lambda key: f"{key}={params[key]}", sorted(params)))
    compare_hash = hmac.new(
        token_hash, str.encode(compare_string), hashlib.sha256
    ).hexdigest()

    return check_hash == compare_hash


@app.route("/")
def hello_world():
    result = ""
    result += (
        f"{validate_telegram_auth(config['TELEGRAM_TOKEN'], request.args.to_dict())}"
    )

    return result

if __name__ == "__main__":
    app.run(debug=True, ssl_context="adhoc", use_reloader=False)
