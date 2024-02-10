import httpx
import pyperclip

from textual.widgets import Static

from messages import DebugMessage, DataReceived
from enums import DebugLevel
from utilities import APIToken


class ActiveMachine(Static):

    token_name = "HTB_TOKEN"
    base_url = "https://labs.hackthebox.com"
    endpoint = {
        "active_machine": "/api/v4/machine/active",
        "active_season_machine": "/api/v4/season/machine/active",
        "active_machine_profile": "/api/v4/machine/profile/",
    }
    headers = {
            "Authorization": f"Bearer {APIToken(token_name).get_token()}",
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "HTBClient/1.0.0"
        }
    
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)                
        self.loading = True
        self.refresh_interval = 10
        self.active_season_machine_id: int = None
        self.active_machine_data = {
            "id": None,
            "status": None, 
            "name": None,
            "os": None,
            "ip": None,
            "difficulty": None,
            "user_owned": None,
            "root_owned": None,
            "points": None,
            "rating": None,
            "release": None,
            "active": None,
            "season_active": None,
            "feedbackForChart": None,
            "user_owns_count": None,
            "root_owns_count": None,
            'playInfo': {
                'isSpawned': None,
                'isSpawning': None,
                'isActive': None,
                'active_player_count': None,
                'expires_at': None
            }
        }

    async def on_mount(self) -> None:
        """Mount the widget."""
        self.loading = True

        self.run_worker(self.update_active_machine())
        self.refresh_active_machine = self.set_interval(self.refresh_interval, self.update_active_machine)

    def _on_click(self) -> None:
        """
        Event handler for when the widget is clicked.
        """
        try:
            pyperclip.copy(self.active_machine_data["ip"])
            self.notify("IP copied to clipboard")
            self.post_message(DebugMessage({"Copied IP": self.active_machine_data["ip"]}, DebugLevel.LOW))
        except Exception as e:
            self.post_message(DebugMessage({"Error": e}, DebugLevel.LOW))

    async def update_active_machine(self) -> None:
        """
        Updates the active machine widget with the latest active machine data from HTB.
        """
        try:
            data = await self.get_active_machine()            
            self.loading = False
            self.post_message(DataReceived(data, "active_machine"))
            self.update(self.make_active_machine())
        except Exception as e:
            self.update(f"Error: {e}")

    async def get_active_machine(self):
        try:
            async with httpx.AsyncClient() as client:
                if self.active_season_machine_id is None:
                    response = await client.get(self.base_url + self.endpoint["active_season_machine"], headers=self.headers)

                    if response.status_code == 200:
                        data = response.json()
                        self.active_season_machine_id = data["data"]["id"]

                response = await client.get(self.base_url + self.endpoint["active_machine"], headers=self.headers)

                if response.status_code == 200:
                    data = response.json()

                    self.post_message(DebugMessage({"Active Machine Data": data}, DebugLevel.HIGH))

                    if data["info"] is None:
                        self.active_machine_data["status"] = "no active machine"
                        self.active_machine_data["id"] = None
                        self.active_machine_data["name"] = None
                        self.active_machine_data["os"] = None
                        self.active_machine_data["ip"] = None
                        self.active_machine_data["difficulty"] = None
                        self.active_machine_data["user_owned"] = False
                        self.active_machine_data["root_owned"] = False
                        self.active_machine_data["points"] = None
                        self.active_machine_data["rating"] = None
                        self.active_machine_data["release"] = None
                        self.active_machine_data["active"] = False
                        self.active_machine_data["season_active"] = False
                        self.active_machine_data["feedbackForChart"] = None
                        self.active_machine_data["user_owns_count"] = None
                        self.active_machine_data["root_owns_count"] = None
                        self.active_machine_data["playInfo"]["isSpawned"] = False
                        self.active_machine_data["playInfo"]["isSpawning"] = False
                        self.active_machine_data["playInfo"]["isActive"] = False
                        self.active_machine_data["playInfo"]["active_player_count"] = 0
                        self.active_machine_data["playInfo"]["expires_at"] = None

                        return self.active_machine_data

                    # assign data to self.active_machine_data
                    self.active_machine_data["status"] = "Active"
                    self.active_machine_data["id"] = data["info"]["id"]
                    if self.active_machine_data["id"] == self.active_season_machine_id:
                        self.active_machine_data["season_active"] = True 
                    else:
                        self.active_machine_data["season_active"] = False
                    self.active_machine_data["name"] = data["info"]["name"]
                    if "ip" in data["info"]:
                        self.active_machine_data["ip"] = data["info"]["ip"]
                    

                    # get additional machine data
                    response = await client.get(self.base_url + self.endpoint["active_machine_profile"] + str(self.active_machine_data["id"]), headers=self.headers)
                    if response.status_code == 200:
                        data = response.json()

                        self.post_message(DebugMessage({"Active Machine Info": data}, DebugLevel.HIGH))

                        # assign data to self.active_machine_data
                        self.active_machine_data["id"] = data["info"]["id"]
                        self.active_machine_data["os"] = data["info"]["os"]
                        self.active_machine_data["difficulty"] = data["info"]["difficultyText"]
                        self.active_machine_data["user_owned"] = data["info"]["authUserInUserOwns"]
                        self.active_machine_data["root_owned"] = data["info"]["authUserInRootOwns"]
                        self.active_machine_data["points"] = data["info"]["points"]
                        self.active_machine_data["rating"] = data["info"]["stars"]
                        self.active_machine_data["release"] = data["info"]["release"]
                        self.active_machine_data["active"] = data["info"]["active"]
                        self.active_machine_data["feedbackForChart"] = data["info"]["feedbackForChart"]
                        self.active_machine_data["user_owns_count"] = data["info"]["user_owns_count"]
                        self.active_machine_data["root_owns_count"] = data["info"]["root_owns_count"]
                        self.active_machine_data["playInfo"]["isSpawned"] = data["info"]["playInfo"]["isSpawned"]
                        self.active_machine_data["playInfo"]["isSpawning"] = data["info"]["playInfo"]["isSpawning"]
                        self.active_machine_data["playInfo"]["isActive"] = data["info"]["playInfo"]["isActive"]
                        self.active_machine_data["playInfo"]["active_player_count"] = data["info"]["playInfo"]["active_player_count"]
                        self.active_machine_data["playInfo"]["expires_at"] = data["info"]["playInfo"]["expires_at"]                        

                        return self.active_machine_data
                else:
                    return f"Error: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Error: {e}"

    def make_active_machine(self):
        if self.active_machine_data["status"] != "Active":
            return f"[b]{self.active_machine_data["status"]}"
        
        if self.active_machine_data["ip"] is None:
            if self.active_machine_data["playInfo"]["isSpawned"]:
                return f"{self.active_machine_data["name"]} :: [#9fef00]spawned"
            if self.active_machine_data["playInfo"]["isSpawning"]:
                return f"{self.active_machine_data["name"]} :: [#9fef00]spawning"
            
            return f"{self.active_machine_data["name"]} :: [#9fef00]{self.active_machine_data["status"]}"
        
        return f"{self.active_machine_data["name"]} :: [#9fef00]{self.active_machine_data["ip"]}"