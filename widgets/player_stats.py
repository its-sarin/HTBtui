import httpx

from rich.table import Table
from rich import box

from textual.widgets import Static

from utilities.api_token import APIToken
from enums.htb_ranks import Ranks
from enums.debug_level import DebugLevel
from messages.debug_message import DebugMessage



class PlayerStats(Static):
    """Static widget that shows the player stats."""

    token_name = "HTB_TOKEN"
    base_url = "https://labs.hackthebox.com"
    endpoint = {
        "info": "/api/v4/user/info",
        "profile": "/api/v4/profile/",
        "season": "/api/v4/season/list",
        "season_rank": "/api/v4/season/user/rank/"
    }
    headers = {
            "Authorization": f"Bearer {APIToken(token_name).get_token()}",
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "HTBClient/1.0.0"
        }

    def __init__(self) -> None:
        super().__init__()        
        self.user_data = {
            "id" : None,
            "name" : None,
            "points" : None,
            "user_owns" : None,
            "system_owns" : None,
            "rank_progress" : None,
            "user_bloods": None,
            "system_bloods": None,
            "respects": None,
        }
        self.current_season = {
            "id" : None,
            "name" : None
        }
        self.season_data = {
            "league": None,
            "rank": None,
            "total_ranks": None,
            "rank_suffix": None,
            "total_season_points": None,
            "flags_to_next_rank": {
                "obtained": None,
                "total": None
            }
        }

    async def on_mount(self) -> None:
        """Mount the widget."""
        self.loading = True
        self.run_worker(self.update_profile())


    async def update_profile(self) -> None:
        """
        Updates the machine list widget with the latest machine list data from HTB.
        """       
        try:
            table: Table = await self.get_profile()
            self.loading = False
            self.parent.border_title = f"{self.user_data['name']} :: {self.user_data['id']}"
            self.parent.styles.border_title_color = "#9fef00"
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

    async def get_profile(self):
        """
        Retrieves the profile data for the user.

        Returns:
            dict: The user's profile data.
        """
        try:
            await self.get_user_id()
            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url + self.endpoint["profile"] + str(self.user_data["id"]), headers=self.headers)
                if response.status_code == 200:
                    data = response.json()

                    self.post_message(DebugMessage({"Profile Data": data}, DebugLevel.MEDIUM))

                    self.user_data["id"] = data['profile']['id']
                    self.user_data["name"] = data['profile']['name']
                    self.user_data["rank"] = data['profile']['rank_id']
                    self.user_data["ranking"] = data['profile']['ranking']
                    self.user_data["points"] = data['profile']['points']
                    self.user_data["user_owns"] = data['profile']['user_owns']
                    self.user_data["system_owns"] = data['profile']['system_owns']
                    self.user_data["rank_progress"] = data['profile']['current_rank_progress']
                    self.user_data["user_bloods"] = data['profile']['user_bloods']
                    self.user_data["system_bloods"] = data['profile']['system_bloods']
                    self.user_data["respects"] = data['profile']['respects']

                    await self.get_current_season()
                    await self.get_season_data()

                    return self.make_profile()
                else:
                    return f"Error: {response.status_code} - {response.text}"
        except Exception as e:
                return f"Error: {e}"
        
    async def get_current_season(self):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url + self.endpoint["season"], headers=self.headers)
                if response.status_code == 200:
                    data = response.json()

                    # iterate over data and find current season
                    for season in data["data"]:
                        if season["active"] == True:
                            self.current_season["id"] = season["id"]
                            self.current_season["name"] = season["name"]

                            return self.current_season

                else:
                    return f"Error: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Error: {e}"
        
    async def get_season_data(self):
        """
        Retrieves the season data for the user.

        """
        try:
            if self.user_data["id"] is None:
                await self.get_user_id()
            if self.current_season["id"] is None:
                await self.get_current_season()

            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url + self.endpoint["season_rank"] + str(self.current_season["id"]), headers=self.headers)
                if response.status_code == 200:
                    data = response.json()

                    self.post_message(DebugMessage({"Season Data": data}, DebugLevel.MEDIUM))

                    # assign data to self.season_data
                    self.season_data["league"] = data["data"]["league"]
                    self.season_data["rank"] = data["data"]["rank"]
                    self.season_data["total_ranks"] = data["data"]["total_ranks"]
                    self.season_data["rank_suffix"] = data["data"]["rank_suffix"]
                    self.season_data["total_season_points"] = data["data"]["total_season_points"]
                    self.season_data["flags_to_next_rank"]["obtained"] = data["data"]["flags_to_next_rank"]["obtained"]
                    self.season_data["flags_to_next_rank"]["total"] = data["data"]["flags_to_next_rank"]["total"]

                    return self.season_data
                else:
                    return f"Error: {response.status_code} - {response.text}"
        except Exception as e:
                return f"Error: {e}"
            

    def id_to_rank(self, id: str) -> str:
        for i, rank in enumerate(Ranks):
            if i == (id-1):
                return rank.value

    def make_profile(self):
        table = Table(
            box=box.SIMPLE, 
            show_header=False, 
            show_footer=False,
            pad_edge=False,
            expand=True
        )

        table.add_column(style="bold", ratio=1)
        table.add_column(style="", ratio=1)

        # user stats
        # table.add_row("Name", f"[#9fef00]{self.user_data["name"]}")
        # table.add_row("ID", str(self.user_data["id"]))
        table.add_row("Rank", self.id_to_rank(self.user_data["rank"]))
        table.add_row("Progress", str(self.user_data["rank_progress"])+ "%")
        table.add_row("Ranking", str(self.user_data["ranking"]))        
        table.add_row("Points", str(self.user_data["points"]))
        table.add_row("User Owns", str(self.user_data["user_owns"]))
        table.add_row("System Owns", str(self.user_data["system_owns"]))
        table.add_row("User Bloods", str(self.user_data["user_bloods"]))
        table.add_row("System Bloods", str(self.user_data["system_bloods"]))
        table.add_row("Respects", str(self.user_data["respects"]))
        
        # season stats
        table.add_row("Season Tier", self.season_data["league"])
        table.add_row("Season Rank", f"{self.season_data["rank"]}/{self.season_data["total_ranks"]}")
        table.add_row("Season Points", str(self.season_data["total_season_points"]))
        table.add_row("Season Flags", f"{self.season_data["flags_to_next_rank"]["obtained"]}/{self.season_data["flags_to_next_rank"]["total"]}")
        
        return table