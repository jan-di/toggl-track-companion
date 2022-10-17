from toggl import Api
from datetime import date, datetime

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

    user = session.merge(user)

    # Fetch all organizations of the user
    organizations = toggl_api.get_my_organizations()
    organizations = list(map(session.merge, organizations))

    # Update organization memberships for user
    for org in organizations:
        user.organizations.append(org)
    session.merge(user)

    # Fetch all workspaces of the user
    workspaces = toggl_api.get_my_workspaces()
    workspaces = list(map(session.merge, workspaces))

    schedule = models.app.Schedule(
        id=3,
        toggl_user_id=8393756,
        toggl_workspace_id=6310682,
        start=datetime.fromisoformat("2021-10-01"),
        day0=28800,
        day1=28800,
        day2=28800,
        day3=28800,
        day4=28800,
        day5=0,
        day6=0,
    )
    session.merge(schedule)

    scheduleex1 = models.app.ScheduleException(
        id=4,
        start=datetime.fromisoformat("2010-10-03"),
        toggl_user_id=8393756,
        toggl_workspace_id=6310682,
        rrule="FREQ=YEARLY;BYMONTH=10",
        factor=0.0,
        description="Tag der deutschen Einheit",
    )
    session.merge(scheduleex1)

    scheduleex2 = models.app.ScheduleException(
        id=5,
        start=datetime.fromisoformat("2022-10-17"),
        toggl_user_id=8393756,
        toggl_workspace_id=6310682,
        rrule="FREQ=DAILY;COUNT=5",
        factor=0.0,
        description="Urlaub",
    )
    session.merge(scheduleex2)

    app_user = models.app.User(
        id=2,
        toggl_user_id=8393756,
        start=date.fromisoformat("2022-10-01"),
        disabled=False,
    )
    session.merge(app_user)

    session.commit()
    session.close()
