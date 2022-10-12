from models.toggl import User
from toggl import Api
from util import load_config, Database

config = load_config()
database = Database(config['DATABASE_URI'])

with database.get_session() as session:
    for toggl_user in session.query(User).all():

        toggl_api = Api(toggl_user.api_token)

        time_entries = toggl_api.get_time_entries(since=11111)

        for te in time_entries:
            session.merge(te)

        session.commit()
        session.flush()
