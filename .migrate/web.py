from app import flask
from app.util import Config


def main():
    config = Config()
    app = flask.create_app(config)

    app.run(debug=True, ssl_context="adhoc", use_reloader=False, host="0.0.0.0")


if __name__ == "__main__":
    main()
