import httpx


class TogglApi:
    def __init__(
        self,
        api_token: str = None,
        username: str = None,
        password: str = None,
        base_url: str = "https://api.track.toggl.com",
    ):
        self.api_token = api_token
        self.username = username
        self.password = password
        self.base_url = base_url
        self.client = httpx.Client()

    def get_me(self) -> tuple[bool, any, int]:
        req = self.__request("GET", "/api/v9/me")
        return self.__response(req)

    # def get_my_organizations(self) -> list[Organization]:
    #     req = self.__request("GET", "/api/v9/me/organizations")
    #     data = req.json()
    #     return list(map(self.__create_organization_from_api, data))

    # def get_my_workspaces(self) -> list[Workspace]:
    #     req = self.__request("GET", "/api/v9/me/all_workspaces")
    #     data = req.json()
    #     return list(map(self.__create_workspace_from_api, data))

    # def get_time_entries(self, since=None, start_date=None, end_date=None):
    #     params = {}
    #     if since is not None:
    #         params["since"] = since
    #     if start_date is not None:
    #         params["start_date"] = start_date
    #     if end_date is not None:
    #         params["end_date"] = end_date

    #     req = self.__request("GET", "/api/v9/me/time_entries", params)
    #     data = req.json()
    #     return list(map(self.__create_time_entry_from_api, data))

    def __request(
        self, method: str, endpoint: str, params: dict = None
    ) -> httpx.Request:
        if params is None:
            params = {}

        if self.api_token:
            auth = (self.api_token, "api_token")
        else:
            auth = (self.username, self.password)

        req = self.client.request(
            method=method,
            params=params,
            url=f"{self.base_url}{endpoint}",
            auth=auth,
        )

        return req

    def __response(self, request: httpx.Request) -> tuple[bool, any, int]:
        success = request.status_code < 300
        if success and request.headers.get("content-type").lower().startswith(
            "application/json"
        ):
            data = request.json()
        else:
            data = request.text
        status = request.status_code

        return success, data, status

    # def __create_user_from_api(self, data: map) -> User:
    #     return User(
    #         id=data["id"],
    #         fullname=data["fullname"],
    #         email=data["email"],
    #         country_id=data["country_id"],
    #         timezone=data["timezone"],
    #         beginning_of_week=data["beginning_of_week"],
    #         image_url=data["image_url"],
    #         created_at=data["created_at"],
    #         updated_at=data["at"],
    #         api_token=data["api_token"],
    #     )

    # def __create_organization_from_api(self, data: map) -> Organization:
    #     return Organization(
    #         id=data["id"],
    #         name=data["name"],
    #         created_at=data["created_at"],
    #         updated_at=data["at"],
    #         deleted_at=data["server_deleted_at"],
    #     )

    # def __create_workspace_from_api(self, data: map) -> Workspace:
    #     return Workspace(
    #         id=data["id"],
    #         organization_id=data["organization_id"],
    #         name=data["name"],
    #         updated_at=data["at"],
    #         deleted_at=data["server_deleted_at"],
    #         logo_url=data["logo_url"],
    #     )

    # def __create_time_entry_from_api(self, data: map) -> TimeEntry:
    #     return TimeEntry(
    #         id=data["id"],
    #         description=data["description"],
    #         start=data["start"],
    #         stop=data["stop"],
    #         updated_at=data["at"],
    #         user_id=data["user_id"],
    #         workspace_id=data["workspace_id"],
    #     )
