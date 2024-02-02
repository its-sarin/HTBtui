import httpx

from rich.table import Table
from rich import box

from textual.widgets import Static

from utilities.api_token import APIToken
from enums.debug_level import DebugLevel
from messages.debug_message import DebugMessage



class PlayerActivity(Static):
    """Static widget that shows the player stats."""

    token_name = "HTB_TOKEN"
    base_url = "https://labs.hackthebox.com"
    endpoint = {
        "info": "/api/v4/user/info",
        "profile_activity": "/api/v4/profile/activity/" # + user_id 
    }
    headers = {
            "Authorization": f"Bearer {APIToken(token_name).get_token()}",
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "HTBClient/1.0.0"
        }

    def __init__(self) -> None:
        super().__init__()
        self.loading = True
        self.user_data = {
            "id" : None,
        }
        self.activity_data = []

    # def on_ready(self) -> None:
    #     self.loading = True

    async def on_mount(self) -> None:
        """Mount the widget."""
        self.loading = True
        self.run_worker(self.update_activity())


    async def update_activity(self) -> None:
        """
        Updates the machine list widget with the latest machine list data from HTB.
        """       
        try:
            table: Table = await self.get_activity_list()
            self.loading = False
            self.update(table)
        except Exception as e:
            self.update(f"Error: {e}")

    async def get_user_id(self) -> str:
        """
        Retrieves the user ID from the API endpoint.

        Returns:
            str: The user ID.
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url + self.endpoint["info"], headers=self.headers)
                if response.status_code == 200:
                    data = response.json()
                    self.user_data["id"] = data['info']['id']

                    return self.user_data["id"]
                else:
                    return f"Error: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Error: {e}"

    async def get_activity_list(self):
            """
            Retrieves the activity list for the player.

            Returns:
                If successful, returns the activity data as a list.
                If an error occurs, returns an error message.
            """
            self.activity_data = []
            try:
                await self.get_user_id()
                async with httpx.AsyncClient() as client:
                    response = await client.get(self.base_url + self.endpoint["profile_activity"] + str(self.user_data["id"]), headers=self.headers)
                    if response.status_code == 200:
                        data = response.json()
                        
                        self.post_message(DebugMessage({"Player Activity": data}, DebugLevel.MEDIUM))

                        self.activity_data = data["profile"]["activity"]

                        return self.make_activity_list()
                        
                    else:
                        return f"Error: {response.status_code} - {response.text}"
            except Exception as e:
                return f"Error: {e}"

    def make_activity_list(self):
        table = Table(
            box=box.SIMPLE,
            show_header=False,
            show_footer=False,
            pad_edge=False,
            expand=True
        )

        table.add_column(ratio=3, no_wrap=True, justify="full")
        table.add_column(ratio=2, no_wrap=True, justify="full")
        table.add_column(ratio=2, no_wrap=True, justify="full")
        table.add_column(ratio=1, no_wrap=True, justify="full")

        for activity in self.activity_data:
            table.add_row(
                f"[b][white]{activity["flag_title"]}" if "flag_title" in activity else f"[b][white]{activity["type"]} flag",
                f"[b]{activity["name"]}[/b] {activity["object_type"]}",
                f"{activity["date_diff"]}",
                f"[chartreuse1]+{activity['points']}pts"
            )

        return table