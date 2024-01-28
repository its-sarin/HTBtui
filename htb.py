import requests
import os
from rich.table import Table
from rich.theme import Theme
from rich.console import Console
from rich import box
import httpx

# Set your Hack The Box API key
# Retrieve API key from environment variable
api_key = os.environ['HTB_API_KEY']

class HTBClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://labs.hackthebox.com"
        self.endpoints = {
            "info": "/api/v4/user/info",
            "profile": "/api/v4/profile/",
            "season": "/api/v4/season/list",
            "season_rank": "/api/v4/season/user/rank/",
            "connection_status": "/api/v4/connection/status",
            "current_machines": "/api/v4/machine/paginated?per_page=100",
            "active_machine": "/api/v4/machine/active",
            "active_season_machine": "/api/v4/season/machine/active",
            "active_machine_info": "/api/v4/machine/info/"
        }
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "HTBClient/1.0.0"
        }
        self.ranks = [
            "Noob",
            "Script Kiddie",
            "[red3]Hacker",
            "[green1]Pro Hacker",
            "Elite Hacker",
            "Guru",
            "Omniscient"
        ]
        self.current_season = {
            "id" : None,
            "name" : None
        }
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
        self.connection_data = {
            "status": None,
            "location_type_friendly": None,
            "server": {
                "id": None,
                "hostname": None,
                "port": None,
                "friendly_name": None
            },
            "connection": {
                "through_pwnbox": None,
                "ip4": None,
                "ip6": None,
                "down": None,
                "up": None
            }
        }
        self.machine_list = []
        self.machine_difficulty_map = {
            "Easy": "chartreuse2",
            "Medium": "gold1",
            "Hard": "indian_red1",
            "Insane": "dark_violet"
        }
        self.machine_os_map = {
            "Linux": ":penguin:",
            "Windows": ":zzz:"
        }
        self.active_machine_data = {
            "status": None, 
            "name": None,
            "os": None,
            "ip": None,
            "difficulty": None,
            "user_owned": None,
            "root_owned": None,
            'playInfo': {
                'isSpawned': None,
                'isSpawning': None,
                'isActive': None,
                'active_player_count': None,
                'expires_at': None
            }
        }


    async def get_user_id(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(self.base_url + self.endpoints["info"], headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                self.user_data["id"] = data['info']['id']

                return self.user_data["id"]
            else:
                print(f"Error: {response.status_code} - {response.text}")


    async def get_profile(self):
        if self.user_data["id"] is None:
            await self.get_user_id()
        async with httpx.AsyncClient() as client:
            response = await client.get(self.base_url + self.endpoints["profile"] + str(self.user_data["id"]), headers=self.headers)
            if response.status_code == 200:
                data = response.json()
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

                return self.user_data
            else:
                print(f"Error: {response.status_code} - {response.text}")


    async def get_current_season(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(self.base_url + self.endpoints["season"], headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                
                # iterate over data and find current season
                for season in data["data"]:
                    if season["active"] == True:
                        self.current_season["id"] = season["id"]
                        self.current_season["name"] = season["name"]
                        
                        return self.current_season

            else:
                print(f"Error: {response.status_code} - {response.text}")


    async def get_season_data(self):
        if self.user_data["id"] is None:
            await self.get_user_id()
        if self.current_season["id"] is None:
            await self.get_current_season()
        async with httpx.AsyncClient() as client:
            response = await client.get(self.base_url + self.endpoints["season_rank"] + str(self.current_season["id"]), headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                
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
                print(f"Error: {response.status_code} - {response.text}")


    async def get_connection_status(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(self.base_url + self.endpoints["connection_status"], headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                # assign data to self.connection_data
                if data != []:
                    self.connection_data["status"] = "Active"
                    self.connection_data["location_type_friendly"] = data[0]["location_type_friendly"]
                    self.connection_data["server"]["id"] = data[0]["server"]["id"]
                    self.connection_data["server"]["hostname"] = data[0]["server"]["hostname"]
                    self.connection_data["server"]["port"] = data[0]["server"]["port"]
                    self.connection_data["server"]["friendly_name"] = data[0]["server"]["friendly_name"]
                    self.connection_data["connection"]["through_pwnbox"] = data[0]["connection"]["through_pwnbox"]
                    self.connection_data["connection"]["ip4"] = data[0]["connection"]["ip4"]
                    self.connection_data["connection"]["ip6"] = data[0]["connection"]["ip6"]
                    self.connection_data["connection"]["down"] = data[0]["connection"]["down"]
                    self.connection_data["connection"]["up"] = data[0]["connection"]["up"]
                    
                    return self.connection_data

                else:
                    self.connection_data["status"] = "No active connection"
                    return self.connection_data["status"]
                
            else:
                # print(f"Error: {response.status_code} - {response.text}")
                self.connection_data["status"] = f"No response: {response.status_code}"
                return self.connection_data["status"]
    
    async def get_machine_list(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(self.base_url + self.endpoints["current_machines"], headers=self.headers)
            if response.status_code == 200:
                data = response.json()

                for machine in data["data"]:
                    self.machine_list.append(
                        {
                            "name": machine["name"],
                            "os": machine["os"],
                            "difficulty": machine["difficultyText"],
                            "user_owned": machine["authUserInUserOwns"],
                            "root_owned": machine["authUserInRootOwns"]
                        }
                    )

                return self.machine_list
            else:
                print(f"Error: {response.status_code} - {response.text}")

    async def get_active_machine(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(self.base_url + self.endpoints["active_machine"], headers=self.headers)
         
            if response.status_code == 200:
                data = response.json()
                
                if data["info"] is None:
                    self.active_machine_data["status"] = "No active machine"
                    self.active_machine_data["name"] = "None"
                    self.active_machine_data["os"] = "None"
                    self.active_machine_data["ip"] = "None"
                    self.active_machine_data["difficulty"] = "None"
                    self.active_machine_data["user_owned"] = False
                    self.active_machine_data["root_owned"] = False
                    self.active_machine_data["playInfo"]["isSpawned"] = False
                    self.active_machine_data["playInfo"]["isSpawning"] = False
                    self.active_machine_data["playInfo"]["isActive"] = False
                    self.active_machine_data["playInfo"]["active_player_count"] = 0
                    self.active_machine_data["playInfo"]["expires_at"] = "None"

                    return data

                # assign data to self.active_machine_data
                self.active_machine_data["status"] = "Active"
                self.active_machine_data["id"] = data["info"]["id"]
                if "ip" in data["info"]:
                    self.active_machine_data["ip"] = data["info"]["ip"] 
                self.active_machine_data["name"] = data["info"]["name"]

                # get additional machine data
                response = await client.get(self.base_url + self.endpoints["active_machine_info"] + str(self.active_machine_data["id"]), headers=self.headers)
                if response.status_code == 200:
                    data = response.json()

                    # assign data to self.active_machine_data
                    self.active_machine_data["os"] = data["info"]["os"]
                    self.active_machine_data["difficulty"] = data["info"]["difficultyText"]
                    self.active_machine_data["user_owned"] = data["info"]["authUserInUserOwns"]
                    self.active_machine_data["root_owned"] = data["info"]["authUserInRootOwns"]
                    self.active_machine_data["playInfo"]["isSpawned"] = data["info"]["playInfo"]["isSpawned"]
                    self.active_machine_data["playInfo"]["isSpawning"] = data["info"]["playInfo"]["isSpawning"]
                    self.active_machine_data["playInfo"]["isActive"] = data["info"]["playInfo"]["isActive"]
                    self.active_machine_data["playInfo"]["active_player_count"] = data["info"]["playInfo"]["active_player_count"]
                    self.active_machine_data["playInfo"]["expires_at"] = data["info"]["playInfo"]["expires_at"]

                    return self.active_machine_data
                else:
                    return self.active_machine_data
            else:
                print(f"Error: {response.status_code} - {response.text}")

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

        table.add_row("Name", self.user_data["name"])
        table.add_row("Rank", self.ranks[self.user_data["rank"]-1])
        table.add_row("Progress", str(self.user_data["rank_progress"])+ "%")
        table.add_row("Ranking", str(self.user_data["ranking"]))        
        table.add_row("Points", str(self.user_data["points"]))
        table.add_row("User Owns", str(self.user_data["user_owns"]))
        table.add_row("System Owns", str(self.user_data["system_owns"]))
        table.add_row("User Bloods", str(self.user_data["user_bloods"]))
        table.add_row("System Bloods", str(self.user_data["system_bloods"]))
        table.add_row("Respects", str(self.user_data["respects"]))
        
        return table
    
    def make_season(self):
        table = Table(
            box=box.SIMPLE, 
            show_header=False, 
            show_footer=False,
            pad_edge=False,
            expand=True
        )

        table.add_column(style="bold", no_wrap=True, ratio=1)
        table.add_column(style="", ratio=1)

        table.add_row("League", self.season_data["league"])
        table.add_row("Rank", f"{self.season_data["rank"]}/{self.season_data["total_ranks"]}")
        table.add_row("Points", str(self.season_data["total_season_points"]))
        table.add_row("Flags", f"{self.season_data["flags_to_next_rank"]["obtained"]}/{self.season_data["flags_to_next_rank"]["total"]}")


        return table
    
    def make_connection(self, refresh=False):
        if refresh:
            self.get_connection_status()
        if self.connection_data["status"] != "Active":
            status = Table.grid(expand=True)
            status.add_column(style="red bold", vertical="middle", justify="center", ratio=1)
            status.add_row(f"{self.connection_data["status"]}")
            return status

        table = Table(
            box=box.SIMPLE,
            show_header=False,
            show_footer=False,
            pad_edge=False,
            expand=True
        )

        table.add_column(style="bold", no_wrap=True)
        table.add_column()

        table.add_row("Location", self.connection_data["location_type_friendly"])
        table.add_row("Server", self.connection_data["server"]["hostname"])
        table.add_row("IP", f"{self.connection_data["connection"]["ip4"]}")
        table.add_row("Pwnbox", f"{self.connection_data["connection"]["through_pwnbox"]}")
        table.add_row("Usage", f"↑ {self.connection_data["connection"]["down"]} : ↓ {self.connection_data["connection"]["up"]}")

        return table
    
    def make_machine_list(self):
        table = Table(
            box=box.SIMPLE,
            show_header=False,
            show_footer=False,
            pad_edge=False,
            expand=True
        )

        table.add_column()
        table.add_column()
        table.add_column()

        for machine in self.machine_list:
            table.add_row(
                machine["name"],
                machine["os"],                                
                "U" if machine["user_owned"] else "",
                "R" if machine["root_owned"] else "",
            )

        return table
    
    def make_active_machine(self, refresh=False):
        if refresh:
            self.get_active_machine()
        if self.active_machine_data["status"] != "Active":
            status = Table.grid(expand=True)
            status.add_column(style="red bold", vertical="middle", justify="center", ratio=1)
            status.add_row(f"{self.active_machine_data["status"]}")
            return status
        table = Table(
            box=box.SIMPLE,
            show_header=False,
            show_footer=False,
            pad_edge=False,
            expand=True
        )

        table.add_column()
        table.add_column()
        table.add_column()
        table.add_column()

        table.add_row(
            self.active_machine_data["name"],
            self.active_machine_data["ip"],
            )
        table.add_row(
            self.active_machine_data["os"],
            self.active_machine_data["difficulty"],
            ":keyboard: " + str(self.active_machine_data["playInfo"]["active_player_count"])
            )
        table.add_row(
            "User", 
            "[x]" if self.active_machine_data["user_owned"] else "[ ]",
            "Root",
             "[x]" if self.active_machine_data["root_owned"] else "[ ]"
            )
        if self.active_machine_data["playInfo"]["isSpawned"]:
            table.add_row(
                "Status", "Spawned"
            )
        elif self.active_machine_data["playInfo"]["isSpawning"]:
            table.add_row(
                "Status", "Spawning"
            )

        # grid.add_row("Expires", self.active_machine_data["playInfo"]["expires_at"])

        return table


if __name__ == "__main__":
    htb = HTBClient(api_key)
    htb.get_profile()

    console = Console()
    
    console.print(htb.make_profile())
# print(htb.get_connection_status())
# htb.print_profile()