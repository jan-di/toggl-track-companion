
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

