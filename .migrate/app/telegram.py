import hashlib
import hmac

from sqlalchemy.orm import Session

from app.models.app import User


def create_or_update_user(session: Session, sender: dict) -> User:
    user = session.query(User).get(sender["id"])

    if not user:
        user = User(sender["id"])
        user.enabled = None
        user.start = None

    user.name = f"{sender['first_name']} {sender['last_name'] if sender['last_name'] is not None else '' }".strip()
    user.username = sender["username"]
    user.language_code = sender["language_code"]

    session.merge(user)
    session.commit()
    session.flush()

    return user


def validate_web_auth(token: str, params: dict[str]) -> bool:
    params = params.copy()
    token_hash = hashlib.sha256(str.encode(token)).digest()
    check_hash = params["hash"]

    for k in list(params.keys()):
        if k.startswith("_"):
            del params[k]

    params.pop("hash")

    compare_string = "\n".join(map(lambda key: f"{key}={params[key]}", sorted(params)))
    compare_hash = hmac.new(
        token_hash, str.encode(compare_string), hashlib.sha256
    ).hexdigest()

    return check_hash == compare_hash
