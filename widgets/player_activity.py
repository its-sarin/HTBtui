import httpx

from textual.widgets import DataTable

from utilities import APIToken
from enums import DebugLevel
from messages import DebugMessage


class PlayerActivity(DataTable):
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

        self.show_header = True
        self.cursor_type = "row"
        
        self.add_column(label="Activity")
        self.add_column(label="Target")
        self.add_column(label="Date")
        self.add_column(label="Points")


    async def on_mount(self) -> None:
        """Mount the widget."""
        self.loading = True
        self.run_worker(self.update_activity())


    async def update_activity(self) -> None:
        """
        Updates the machine list widget with the latest machine list data from HTB.
        """       
        try:
            await self.get_activity_list()
            self.loading = False
            self.make_activity_list()
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
        for activity in self.activity_data:
            self.add_row(
                f"[b]{activity["flag_title"]}" if "flag_title" in activity else f"[b]{activity["type"]}",
                f"[b]{activity["name"]}[/b]",
                # {activity['object_type']}
                f"{activity["date_diff"]}",
                f"[#9fef00]+{activity['points']}pts"
            )