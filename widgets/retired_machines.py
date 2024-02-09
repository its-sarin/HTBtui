import httpx

from textual.widgets import DataTable

from utilities import APIToken
from enums import DebugLevel
from messages import DebugMessage

class RetiredMachines(DataTable):
    """DataTable widget that shows retired machines."""

    token_name = "HTB_TOKEN"
    base_url = "https://labs.hackthebox.com"
    endpoint = "/api/v4/machine/list/retired/paginated?per_page=100"
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
        self.machine_data = {}
        self.loading = True
        self.id = "retired_machines"
        self.show_header = True
        self.cursor_type = "row"

        # Initialize the data table columns
        
        self.add_column(label="ID")
        self.add_column(label="Name")
        self.add_column(label="OS")
        # self.add_column(label="Difficulty")
        self.add_column(label="User")
        self.add_column(label="Root")
        self.add_column(label="Points")
        self.add_column(label="Rating")


    async def on_mount(self) -> None:
        """Mount the widget."""
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
        self.machine_list = []
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url + self.endpoint, headers=self.headers)
                if response.status_code == 200:
                    data = response.json()

                    self.post_message(DebugMessage({"Current Machines": data}, DebugLevel.MEDIUM))

                    for machine in data["data"]:
                        self.machine_data[machine["id"]] = {
                                "name": machine["name"],
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

                    return self.machine_data
                else:
                    return f"Error: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Error: {e}"
        
    # def on_data_table_row_selected(self, data_table: DataTable, cursor_row, row_key) -> None:
    #     """
    #     Event handler for when a row in the data table is selected.

    #     Args:
    #         row (int): The index of the selected row.
    #         data (dict): The data associated with the selected row.
    #     """
    #     self.post_message(DebugMessage({"Selected Machine": data}, DebugLevel.MEDIUM))

    def make_machine_list(self):
        """ 
        iterate over the machine list and add a row for each machine

        Data example:
        {
            580: {
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
                key=f"{id}")