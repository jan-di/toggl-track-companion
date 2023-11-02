# from src.toggl.api import TogglApi

# tapi = TogglApi("11147e8c6146b034373d740c227c47a5")

# print(tapi.get_me())

from src.db.entity import Tag
from src.toggl.model import TagData

td = TagData()

user = Tag()
user.create_or_update_tag_from_api(td)