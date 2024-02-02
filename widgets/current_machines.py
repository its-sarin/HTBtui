import httpx

from rich.table import Table
from rich import box

from textual.widgets import Static

from utilities.api_token import APIToken
from enums.debug_level import DebugLevel
from messages.debug_message import DebugMessage

class CurrentMachines(Static):
    """Static widget that shows the current machines."""

    token_name = "HTB_TOKEN"
    base_url = "https://labs.hackthebox.com"
    endpoint = "/api/v4/machine/paginated?per_page=100"
    headers = {
            "Authorization": f"Bearer {APIToken(token_name).get_token()}",
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "HTBClient/1.0.0"
        }

    def __init__(self) -> None:
        super().__init__()        
        self.machine_list = []
        self.loading = True

    async def on_mount(self) -> None:
        """Mount the widget."""
        self.run_worker(self.update_machine_list())


    async def update_machine_list(self) -> None:
        """
        Updates the machine list widget with the latest machine list data from HTB.
        """       
        try:
            table: Table = await self.get_machine_list()
            self.loading = False
            self.update(table)
        except Exception as e:
            self.update(f"Error: {e}")

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
                                "rating": machine["star"]
                            }
                        )

                    return self.make_machine_list()
                else:
                    return f"Error: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Error: {e}"

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
        table.add_column()
        table.add_column()
        table.add_column()
        table.add_column()

        for machine in self.machine_list:
            table.add_row(
                str(machine["id"]),
                machine["name"],
                machine["os"],    
                machine["difficulty"],                            
                "[chartreuse1 bold]owned user" if machine["user_owned"] else "",
                "[chartreuse1 bold]owned root" if machine["root_owned"] else "",
                str(machine["rating"])
            )

        return table