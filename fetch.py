import logging
from app.models.app import User
from app.toggl import Api
from app.util import Config, Database

config = Config()
database = Database(config.database_uri)
logging.basicConfig(level=logging.INFO)

with database.get_session() as session:
    for user in session.query(User).all():
        toggl_user = user.toggl_user

        if toggl_user is None:
            continue

        logging.info("user %s", toggl_user.fullname)

        toggl_api = Api(toggl_user.api_token)

        # Fetch all organizations of the user
        organizations = toggl_api.get_my_organizations()
        organizations = list(map(session.merge, organizations))

        # Update organization memberships for user
        for org in organizations:
            toggl_user.organizations.append(org)
        session.merge(toggl_user)

        # Fetch all workspaces of the user
        workspaces = toggl_api.get_my_workspaces()
        workspaces = list(map(session.merge, workspaces))

        # Fetch time entries of the user
        time_entries = toggl_api.get_time_entries()
        time_entries = list(map(session.merge, time_entries))

        session.commit()
        session.flush()
