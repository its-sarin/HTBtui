import httpx

from textual.widgets import DataTable
from textual.reactive import Reactive

from utilities.api_token import APIToken
from enums.debug_level import DebugLevel
from messages.debug_message import DebugMessage

class SeasonalMachines(DataTable):
    """DataTable widget that shows the seasonal machines."""
    

    token_name = "HTB_TOKEN"
    base_url = "https://labs.hackthebox.com"
    endpoints = {
        "seasonal_machines": "/api/v4/season/machines",
        "seasons_list": "/api/v4/season/list"
    }
    headers = {
            "Authorization": f"Bearer {APIToken(token_name).get_token()}",
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "HTBClient/1.0.0"
        }
    machine_difficulty_map = {
            "Easy": "#90cd3f",
            "Medium": "#ffb83e",
            "Hard": "#fe0000",
            "Insane": "#ffccff"
        }
    active_season_id: int = Reactive(0)
    active_season_name: str = Reactive("")

    def __init__(self) -> None:
        super().__init__()        
        self.loading = True
        self.id = "seasonal_machines"
        self.machine_data = {}
        self.active_ids = []
        self.show_header = True
        self.cursor_type = "row"

        # Initialize the data table columns
        
        self.add_column(label="ID")
        self.add_column(label="Name")
        self.add_column(label="OS")
        self.add_column(label="User")
        self.add_column(label="Root")
        self.add_column(label="Status")
        self.add_column(label="Week")


    def watch_active_season_name(self, old_value:str, new_value: str) -> None:
        self.post_message(DebugMessage({"Seasonal Machines": f"Active Season: {new_value}"}, DebugLevel.LOW))

    async def on_mount(self) -> None:
        """Mount the widget."""
        self.run_worker(self.update_machine_list()) 
        self.run_worker(self.get_seasons_list())       

    async def reload_machines(self) -> None:
        """Reload the machines."""
        self.loading = True
        self.run_worker(self.update_machine_list())

    async def get_seasons_list(self):
        """
        Retrieves the list of seasons from the server.

        Returns:
            list: A list of dictionaries representing the seasons, each containing the following keys:
                - id (int): The ID of the season.
                - name (str): The name of the season.
        
        Raises:
            str: An error message if an exception occurs during the retrieval process.
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url + self.endpoints["seasons_list"], headers=self.headers)
                if response.status_code == 200:
                    data = response.json()

                    for season in data["data"]:
                        if season["active"]:
                            self.active_season_id = season["id"]
                            self.active_season_name = season["name"]
                            break

                    return data["data"]
                else:
                    return f"Error: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Error: {e}"

    async def update_machine_list(self) -> None:
        """
        Updates the machine list widget with the latest machine list data from HTB.
        """       
        try:
            await self.get_machine_list()
            self.post_message(DebugMessage({"Seasonal Machines": self.machine_data}, DebugLevel.LOW))
            self.loading = False
            self.make_machine_list()
        except Exception as e:
            self.post_message(DebugMessage({"Seasonal Machines Error": f"Error: {e}"}, DebugLevel.LOW))
            return f"Error: {e}"

    async def get_machine_list(self):
        """
        Retrieves the list of machines from the server.

        Returns:
            list: A list of dictionaries representing the machines, each containing the following keys:
                - name (str): The name of the machine.
                - os (str): The operating system of the machine.
                - difficulty (str): The difficulty level of the machine.
                - user_owned (bool): Indicates whether the authenticated user owns the machine.
                - root_owned (bool): Indicates whether the authenticated user has root access to the machine.
        
        Raises:
            str: An error message if an exception occurs during the retrieval process.
        """
        self.machine_data = {}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url + self.endpoints["seasonal_machines"], headers=self.headers)
                if response.status_code == 200:
                    data = response.json()
                    
                    self.machine_data = data["data"]

                    for machine in self.machine_data:
                        if machine["is_released"]:
                            self.active_ids.append(machine["id"])

                    return self.machine_data
                else:
                    return f"Error: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Error: {e}"

    def make_machine_list(self):
        """ 
        iterate over the machine list and add a row for each machine

        Data example:
        {
            "580": {
                "name": "Bashed",
                "os": "Linux",
                "difficulty": "Easy",
                "user_owned": false,
                "root_owned": false,
                "points": 20,
                "rating": 3.4
            }
        }
        """
            
        for i, data in enumerate(self.machine_data):
            if not data["unknown"] and data["is_released"]:
                self.add_row(                
                    str(data["id"]),
                    f"[{self.machine_difficulty_map[data['difficulty_text']]}]{data['name']}",
                    data['os'],    
                    "✅" if data['is_owned_user'] else "❌",
                    "✅" if data['is_owned_root'] else "❌",
                    "Active" if data['active'] else "Expired",
                    f"Week {i+1}",
                    key=data["id"])
            elif not data["unknown"] and not data["is_released"]:
                self.add_row(                
                    str(data["id"]),
                    f"[{self.machine_difficulty_map[data['difficulty_text']]}]{data['name']}",
                    "❓",    
                    "✖️",
                    "✖️",
                    "~",
                    f"Week {i+1}",
                    key=data["id"])
            if data["unknown"]:
                self.add_row(                
                    "❓",
                    "???",    
                    "❓",
                    "✖️",
                    "✖️",
                    "~",
                    f"Week {i+1}")
            