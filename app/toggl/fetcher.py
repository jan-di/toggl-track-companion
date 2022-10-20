from datetime import date
from dateutil.relativedelta import relativedelta
from app.models.toggl import User
from app.toggl import Api


class Fetcher:
    def __init__(self, session, user: User):
        self.user = user
        self.session = session
        self.toggl_api = Api(user.api_token)

    def update_organizations(self):
        organizations = self.toggl_api.get_my_organizations()
        organizations = list(map(self.session.merge, organizations))

        for org in organizations:
            self.user.organizations.append(org)
        self.session.merge(self.user)

        self.session.commit()
        self.session.flush()

        return organizations

    def update_workspaces(self):
        workspaces = self.toggl_api.get_my_workspaces()
        workspaces = list(map(self.session.merge, workspaces))

        self.session.commit()
        self.session.flush()

        return workspaces

    def update_timeentries(self):
        today = date.today()
        start_date = today + relativedelta(months=-3) + relativedelta(days=1)
        end_date = today + relativedelta(days=1)

        time_entries = self.toggl_api.get_time_entries(
            start_date=start_date, end_date=end_date
        )
        time_entries = list(map(self.session.merge, time_entries))

        self.session.commit()
        self.session.flush()

        return time_entries
