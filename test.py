from toggl import Api

from util import load_config, Database

# pylint: disable=unused-import
import models.toggl
import models.telegram
import models.app

config = load_config()
database = Database(config["DATABASE_URI"])

database.Base.metadata.drop_all(database.engine)
database.Base.metadata.create_all(database.engine)

with database.get_session() as session:

    toggl_api = Api(config["TOGGL_TOKEN"])
    user = toggl_api.get_me()

    session.merge(user)

    session.commit()
    session.close()
