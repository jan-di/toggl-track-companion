import sys
from datetime import date, datetime

from app.toggl import Api
from app.util import Config, Database
from app.models.app import Schedule, ScheduleException

config = Config()
database = Database(config.database_uri)


def create_schema():
    database.orm_base.metadata.create_all(database.engine)


def drop_schema():
    database.orm_base.metadata.drop_all(database.engine)


def init_test_data():  # to be removed
    with database.get_session() as session:
        toggl_api = Api(config.toggl_token)
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

        schedule = Schedule(
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

        scheduleex1 = ScheduleException(
            id=4,
            start=date.fromisoformat("2010-10-03"),
            toggl_user_id=8393756,
            toggl_workspace_id=6310682,
            rrule="FREQ=YEARLY;BYMONTH=10",
            factor=0.0,
            description="Tag der deutschen Einheit",
        )
        session.merge(scheduleex1)

        scheduleex2 = ScheduleException(
            id=5,
            start=date.fromisoformat("2022-10-17"),
            toggl_user_id=8393756,
            toggl_workspace_id=6310682,
            rrule="FREQ=DAILY;COUNT=5",
            factor=0.0,
            description="Urlaub",
        )
        session.merge(scheduleex2)

        session.commit()
        session.close()


if __name__ == "__main__":
    args = sys.argv

    globals()[args[1]](*args[2:])
