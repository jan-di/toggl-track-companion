# from re import X
# import httpx
# import datetime
from models.toggl import User
from util import load_config, Database

config = load_config()
database = Database(config["DATABASE_URI"])

with database.get_session() as session:
    for user in session.query(User).all():
        for organization in user.organizations:
            for workspace in organization.workspaces:

                print(f"{user.fullname} > {organization.name} > {workspace.name}")


# print(req.status_code)


# class Week():
#     def init(self, year, week, targetHours):
#         self.year = year
#         self.week = week
#         self.targetHours = targetHours
#         self.timeEntries = []

#     def totalTargetTime(self):
#         return sum(self.targetHours) * pow(60, 2)

# # start_date -> fix vom profil nehmen
# # end_date -> aktuelles datum - 1 (-> der aktuellste vollständige tag)

# weeks = {}
# for te in req.json():
#     # print(te)

#     dt = datetime.datetime.fromisoformat(te['start'])
#     kw = dt.isocalendar()

#     if not (kw.year, kw.week) in weeks:
#         weeks[kw.year, kw.week] = Week(kw.year, kw.week, [8, 8, 8, 8, 8, 0, 0])

#     # print(te)
#     # print("---")

#     weeks[kw.year, kw.week].timeEntries.append(te)

# runningSum = 0
# for key, val in weeks.items():

#     realWork = sum(c['duration'] for c in val.timeEntries)
#     targetWork = val.totalTargetTime()
#     difference = realWork - targetWork
#     runningSum += difference

#     print(
#         f"{key} -> I: {realWork/(60*60)} S: {targetWork/(60*60)} D: {difference/(60*60)} -> {runningSum/(60*60)}")
#     exit

# # print(weeks)
