from datetime import datetime

from textual.widgets import Static, Button

from rich.table import Table

from utilities.api_token import APIToken
from enums.debug_level import DebugLevel
from messages.debug_message import DebugMessage

class MachineControl(Static):
    """Static widget that shows the current machines."""

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
        self.selected_machine_id = None
        self.selected_machine_data = {}        
        self.border_title = "Machine Details"
        # self.loading = True

    async def on_mount(self) -> None:
        """Mount the widget."""
        # self.loading = True


    def set_context(self, machine_id: str, machine_data: dict) -> None:
        """
        Selects a machine from the list of current machines.
        """
        self.selected_machine_id = machine_id
        self.selected_machine_data = machine_data
        self.border_title = f"{self.selected_machine_data['name']} :: {self.selected_machine_id}"
        self.styles.border_title_color = "#9fef00"
        self.update(self.make_machine_details())

    def clear_context(self) -> None:
        """
        Clears the selected machine context.
        """
        self.selected_machine_id = None
        self.selected_machine_data = {}
        self.refresh()

    def get_context(self) -> dict:
        """
        Returns the selected machine context.
        """
        return self.selected_machine_data
    
    def make_machine_details(self) -> None:
        """
        Makes the machine details.
        """
        table = Table.grid(expand=True)

        table.add_column(justify="justify")

        """
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
        """

        table.add_row(self.selected_machine_data["os"])
        table.add_row(f"[{self.machine_difficulty_map[self.selected_machine_data['difficulty']]}]{self.selected_machine_data["difficulty"]}")
        
        if self.selected_machine_data["user_owned"]:
            table.add_row("User owned")
        if self.selected_machine_data["root_owned"]:
            table.add_row("Root owned")
        
        table.add_row(f"{self.selected_machine_data["points"]} points")
        table.add_row(f"{self.selected_machine_data["rating"]} stars")

        # convert release date string to human readable format
        release_date = datetime.strptime(self.selected_machine_data["release"], "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%B %d, %Y")
        table.add_row(release_date)

        if self.selected_machine_data["active"]:
            table.add_row("Active")

        # table.add_row("Labels", self.selected_data["labels"])
        # table.add_row("Feedback", self.selected_data["feedbackForChart"])
            
        if self.selected_machine_data["is_competitive"]:
            table.add_row("Competitive")

        table.add_row("User Owns", str(self.selected_machine_data["user_owns_count"]))
        table.add_row("Root Owns", str(self.selected_machine_data["root_owns_count"]))

        return table


    # async def start_machine(self) -> None:
    #     """
    #     Starts the selected machine.
    #     """
    #     try:
    #         await self.start_machine_request()
    #         self.clear_context()
    #     except Exception as e:
    #         DebugMessage(
    #             DebugLevel.ERROR, 
    #             f"Failed to start machine: {e}"
    #         )
