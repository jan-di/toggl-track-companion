from models.toggl import User
from toggl import Api
from util import load_config, Database

config = load_config()
database = Database(config["DATABASE_URI"])

with database.get_session() as session:
    for toggl_user in session.query(User).all():

        session.merge(toggl_user)

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
