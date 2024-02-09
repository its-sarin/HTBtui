import httpx

from textual.widgets import DataTable

from utilities import APIToken
from enums import DebugLevel
from messages import DebugMessage

class CurrentMachines(DataTable):
    """DataTable widget that shows the current machines."""

    token_name = "HTB_TOKEN"
    base_url = "https://labs.hackthebox.com"
    endpoint = "/api/v4/machine/paginated?per_page=100"
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

    def __init__(self) -> None:
        super().__init__()        
        self.loading = True
        self.id = "current_machines"
        self.machine_data = {}
        self.show_header = True
        self.cursor_type = "row"

        # Initialize the data table columns
        
        self.add_column(label="ID")
        self.add_column(label="Name")
        self.add_column(label="OS")
        self.add_column(label="User")
        self.add_column(label="Root")
        self.add_column(label="Points")
        self.add_column(label="Rating")


    async def on_mount(self) -> None:
        """Mount the widget."""
        self.run_worker(self.update_machine_list())

    async def reload_machines(self) -> None:
        """Reload the machines."""
        self.loading = True
        self.run_worker(self.update_machine_list())

    async def update_machine_list(self) -> None:
        """
        Updates the machine list widget with the latest machine list data from HTB.
        """       
        try:
            await self.get_machine_list()
            self.loading = False
            self.make_machine_list()
        except Exception as e:
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
                response = await client.get(self.base_url + self.endpoint, headers=self.headers)
                if response.status_code == 200:
                    data = response.json()

                    self.post_message(DebugMessage({"Current Machines": data}, DebugLevel.MEDIUM))

                    """
                        {
                            "id": 584,
                            "avatar": "/storage/avatars/c31f19a4d6a3be17987a3ef98e2446a5.png",
                            "name": "Analysis",
                            "static_points": 40,
                            "sp_flag": 0,
                            "os": "Windows",
                            "points": 40,
                            "star": 4.2,
                            "release": "2024-01-20T17:00:00.000000Z",
                            "easy_month": 0,
                            "poweroff": 0,
                            "free": true,
                            "difficulty": 61,
                            "difficultyText": "Hard",
                            "user_owns_count": 881,
                            "authUserInUserOwns": false,
                            "root_owns_count": 775,
                            "authUserHasReviewed": false,
                            "authUserInRootOwns": false,
                            "isTodo": false,
                            "is_competitive": true,
                            "active": null,
                            "feedbackForChart": {
                                "counterCake": 26,
                                "counterVeryEasy": 15,
                                "counterEasy": 53,
                                "counterTooEasy": 94,
                                "counterMedium": 190,
                                "counterBitHard": 197,
                                "counterHard": 307,
                                "counterTooHard": 142,
                                "counterExHard": 43,
                                "counterBrainFuck": 37
                            },
                            "ip": null,
                            "playInfo": {
                                "isActive": null,
                                "expires_at": null
                            },
                            "labels": [
                                {
                                    "color": "blue",
                                    "name": "SEASONAL"
                                }
                            ],
                            "recommended": 0
                        }
                    """
                    for machine in data["data"]:
                        self.machine_data[machine["id"]] = {
                                "name": machine["name"],
                                "id": machine["id"],
                                "os": machine["os"],
                                "difficulty": machine["difficultyText"],
                                "user_owned": machine["authUserInUserOwns"],
                                "root_owned": machine["authUserInRootOwns"],
                                "points": machine["points"],
                                "rating": machine["star"],
                                "release": machine["release"],
                                "active": machine["active"],
                                "labels": machine["labels"],
                                "feedbackForChart": machine["feedbackForChart"],
                                "is_competitive": machine["is_competitive"],
                                "user_owns_count": machine["user_owns_count"],
                                "root_owns_count": machine["root_owns_count"],
                            }
                                                            
                        
                    print(f"Machine Data: {self.machine_data}")
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
            
        for id, data in self.machine_data.items():
            self.add_row(                
                str(id),
                f"[{self.machine_difficulty_map[data['difficulty']]}]{data['name']}",
                data['os'],    
                "✅" if data['user_owned'] else "❌",
                "✅" if data['root_owned'] else "❌",
                str(data['points']),
                str(data['rating']),
                key=id)
            