import httpx

from textual.widgets import DataTable, Button

from utilities.api_token import APIToken
from enums.debug_level import DebugLevel
from messages.debug_message import DebugMessage

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

    def __init__(self) -> None:
        super().__init__()        
        self.machine_list = []
        self.loading = True
        self.show_header = True
        self.cursor_type = "row"

        # Initialize the data table columns
        
        self.add_column(label="ID")
        self.add_column(label="Name")
        self.add_column(label="OS")
        self.add_column(label="Difficulty")
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
                        self.machine_list.append(
                            {
                                "id": machine["id"],
                                "name": machine["name"],
                                "os": machine["os"],
                                "difficulty": machine["difficultyText"],
                                "user_owned": machine["authUserInUserOwns"],
                                "root_owned": machine["authUserInRootOwns"],
                                "points": machine["points"],
                                "rating": machine["star"]
                            }
                        )

                    return self.make_machine_list()
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
        for machine in self.machine_list:
            self.add_row(                
                str(machine["id"]),
                machine["name"],
                machine["os"],    
                machine["difficulty"],                            
                "✅" if machine["user_owned"] else "❌",
                "✅" if machine["root_owned"] else "❌",
                str(machine["points"]),
                str(machine["rating"]),
                key=f"{machine['id']}")
            

        # self.sort_reverse(
        #     "ID",
        #     key=lambda id: int(id)
        # )