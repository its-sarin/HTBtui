import httpx

from rich.table import Table
from rich import box

from textual.widgets import Static

from messages.debug_message import DebugMessage
from enums.debug_level import DebugLevel
from utilities.api_token import APIToken


class ActiveMachine(Static):

    token_name = "HTB_TOKEN"
    base_url = "https://labs.hackthebox.com"
    endpoint = {
        "active_machine": "/api/v4/machine/active",
        "active_season_machine": "/api/v4/season/machine/active",
        "active_machine_info": "/api/v4/machine/info/",
    }
    headers = {
            "Authorization": f"Bearer {APIToken(token_name).get_token()}",
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "HTBClient/1.0.0"
        }
    
    def __init__(self) -> None:
        super().__init__()                
        self.loading = True
        self.refresh_interval = 5
        self.active_machine_data = {
            "id": None,
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

    async def on_mount(self) -> None:
        """Mount the widget."""
        self.loading = True

        self.run_worker(self.update_active_machine())
        self.refresh_active_machine = self.set_interval(self.refresh_interval, self.update_active_machine)


    async def update_active_machine(self) -> None:
        """
        Updates the active machine widget with the latest active machine data from self.htb.
        """
        try:
            table: Table = await self.get_active_machine()
            self.loading = False
            self.update(table)
        except Exception as e:
            self.update(f"Error: {e}")

    async def get_active_machine(self):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url + self.endpoint["active_machine"], headers=self.headers)

                if response.status_code == 200:
                    data = response.json()

                    self.post_message(DebugMessage({"Active Machine Data": data}, DebugLevel.HIGH))

                    if data["info"] is None:
                        self.active_machine_data["status"] = "No active machine"
                        self.active_machine_data["id"] = None
                        self.active_machine_data["name"] = None
                        self.active_machine_data["os"] = None
                        self.active_machine_data["ip"] = None
                        self.active_machine_data["difficulty"] = None
                        self.active_machine_data["user_owned"] = False
                        self.active_machine_data["root_owned"] = False
                        self.active_machine_data["playInfo"]["isSpawned"] = False
                        self.active_machine_data["playInfo"]["isSpawning"] = False
                        self.active_machine_data["playInfo"]["isActive"] = False
                        self.active_machine_data["playInfo"]["active_player_count"] = 0
                        self.active_machine_data["playInfo"]["expires_at"] = None

                        return self.make_active_machine()

                    # assign data to self.active_machine_data
                    self.active_machine_data["status"] = "Active"
                    self.active_machine_data["id"] = data["info"]["id"]
                    if "ip" in data["info"]:
                        self.active_machine_data["ip"] = data["info"]["ip"]
                    self.active_machine_data["name"] = data["info"]["name"]

                    # get additional machine data
                    response = await client.get(self.base_url + self.endpoint["active_machine_info"] + str(self.active_machine_data["id"]), headers=self.headers)
                    if response.status_code == 200:
                        data = response.json()

                        self.post_message(DebugMessage({"Active Machine Info": data}, DebugLevel.HIGH))

                        # assign data to self.active_machine_data
                        self.active_machine_data["id"] = data["info"]["id"]
                        self.active_machine_data["os"] = data["info"]["os"]
                        self.active_machine_data["difficulty"] = data["info"]["difficultyText"]
                        self.active_machine_data["user_owned"] = data["info"]["authUserInUserOwns"]
                        self.active_machine_data["root_owned"] = data["info"]["authUserInRootOwns"]
                        self.active_machine_data["playInfo"]["isSpawned"] = data["info"]["playInfo"]["isSpawned"]
                        self.active_machine_data["playInfo"]["isSpawning"] = data["info"]["playInfo"]["isSpawning"]
                        self.active_machine_data["playInfo"]["isActive"] = data["info"]["playInfo"]["isActive"]
                        self.active_machine_data["playInfo"]["active_player_count"] = data["info"]["playInfo"]["active_player_count"]
                        self.active_machine_data["playInfo"]["expires_at"] = data["info"]["playInfo"]["expires_at"]

                        return self.make_active_machine()
                else:
                    return f"Error: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Error: {e}"

    def make_active_machine(self):
        if self.active_machine_data["status"] != "Active":
            return f"[b]{self.active_machine_data["status"]}"
        table = Table(
            box=box.SIMPLE,
            show_header=False,
            show_footer=False,
            pad_edge=False,
            expand=True
        )

        table.add_column()
        table.add_column()
        table.add_column(justify="left")

        table.add_row(
            self.active_machine_data["name"],
            f"[#37ff0f]{self.active_machine_data["ip"]}",
            f"# Players {self.active_machine_data["playInfo"]["active_player_count"]}"
            )
        table.add_row(
            self.active_machine_data["os"],
            self.active_machine_data["difficulty"],
           
            )
        table.add_row(
            "User [green1]☑" if self.active_machine_data["user_owned"] else "User [white]☐",
            "Root [green1]☑" if self.active_machine_data["root_owned"] else "Root [white]☐"
            )
        if self.active_machine_data["playInfo"]["isSpawned"]:
            table.add_row(
                "Status", "[green1]Spawned"
            )
        elif self.active_machine_data["playInfo"]["isSpawning"]:
            table.add_row(
                "Status", "[yellow3]Spawning"
            )
        # table.add_row("Expires", self.active_machine_data["playInfo"]["expires_at"])

        return table

    def handle_active_machine(self) -> None:
        """
        Handles the active machine.

        If there is an active machine, it writes the machine details to the log and starts pinging the machine at regular intervals.
        If there is no active machine, it stops pinging the machine (if already started).
        """
        if self.active_machine_data["id"] is not None:
            if self.has_active_machine:
                return
            
            self.has_active_machine = True

            log = self.app.query_one(RichLog)
            log.write("\n")
            log.write("[+] Active machine found")
            log.write(f"[*] Name: {self.active_machine_data['name']}")
            log.write(f"[*] IP: {self.active_machine_data['ip']}")
            log.write(f"[*] OS: {self.active_machine_data['os']}")
            log.write(f"[*] Difficulty: {self.active_machine_data['difficulty']}")
            log.write("\n")

            self.refresh_active_machine_ping = self.set_interval(
                self.PING_INTERVAL,
                self.ping_active_machine
                )
        else:
            self.has_active_machine = False
            if self.refresh_active_machine_ping is not None:
                self.refresh_active_machine_ping.stop()
