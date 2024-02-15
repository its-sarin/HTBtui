import httpx

from rich.table import Table
from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static, ProgressBar, Label

from utilities import APIToken
from enums import Ranks, DebugLevel
from messages import DebugMessage



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
    
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)        
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

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        
        with Container(id="player_stats_container"):
            yield Label(id="player_rank_label")
            yield ProgressBar(id="player_rank_progress", show_percentage=True, show_eta=False, total=100)
            yield Label(id="player_rank_progress_label")
            yield Static(id="player_stats_table")


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
            cntr = self.query_one("#player_stats_container")
            cntr.border_title = f"👤{self.user_data['name']}::{self.user_data['id']}"
            cntr.styles.border_title_color = "#9fef00"
            self.query_one("#player_rank_label").update(self.id_to_rank(self.user_data["rank"]))
            self.query_one("#player_stats_table").update(table)
            self.query_one("#player_rank_progress", ProgressBar).advance(self.user_data["rank_progress"])
            self.query_one("#player_rank_progress_label").update(self.id_to_rank(self.user_data['rank']+1))
            self.loading = False
            
        except Exception as e:
            self.query_one("#player_stats_table").update(f"Error: {e}")

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

        table = Table.grid(
            pad_edge=False,
            expand=True
        )

        table.add_column(ratio=1)
        table.add_column(ratio=1)


        table.add_row(f"Rank: #{self.user_data['ranking']}", f"Points: {self.user_data['points']}") 
        table.add_row()       
        table.add_row(f"User 🏳️ : {self.user_data['user_owns']}", f"System 🏳️ : {self.user_data['system_owns']}")
        table.add_row(f"User 🩸: {self.user_data['user_bloods']}", f"System 🩸: {self.user_data['system_bloods']}")
        table.add_row()
        table.add_row("Respects", f"{self.user_data['respects']}")
        table.add_row()
        
        # season stats
        table.add_row("Season Tier", self.season_data['league'])
        table.add_row("Season Rank", f"{self.season_data['rank']}/{self.season_data['total_ranks']}")
        table.add_row("Season Points", str(self.season_data['total_season_points']))
        table.add_row("Season Flags", f"{self.season_data['flags_to_next_rank']['obtained']}/{self.season_data['flags_to_next_rank']['total']}")
        
        return table