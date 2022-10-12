import httpx

from models.toggl import User, TimeEntry


class Api:
    def __init__(self, api_token, base_url="https://api.track.toggl.com"):
        self.api_token = api_token
        self.base_url = base_url
        self.client = httpx.Client()

    def get_me(self) -> User:
        req = self.__request('GET', '/api/v9/me')

        data = req.json()
        return User.create_from_data(data)

    def get_time_entries(self, since=None):
        """
        GET TimeEntries
        https://developers.track.toggl.com/docs/api/time_entries#get-timeentries
        """

        params = {}
        if since is not None:
            params["since"] = since

        req = self.__request('GET', '/api/v9/me/time_entries', params)

        data = req.json()

        time_entries = []
        for element in data:
            time_entries.append(TimeEntry.create_from_data(element))
        return time_entries

    def __request(self, method, endpoint, params=None):
        if params is not None:
            params = {}

        req = self.client.request(
            method=method,
            params=params,
            url=f"{self.base_url}{endpoint}",
            auth=(self.api_token, "api_token"),
        )

        return req
