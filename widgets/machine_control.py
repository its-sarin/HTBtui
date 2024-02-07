import httpx
from datetime import datetime
from textual import on
from textual.app import ComposeResult
from textual.widgets import Static, Button
from textual.containers import Container
from textual.reactive import Reactive

from rich.table import Table

from utilities.api_token import APIToken
from enums.debug_level import DebugLevel
from messages.debug_message import DebugMessage
from messages.log_message import LogMessage
from messages.data_received import DataReceived


class MachineDetails(Static):
    """Static widget that shows the current machines."""

    token_name = "HTB_TOKEN"
    base_url = "https://labs.hackthebox.com"
    endpoint = "/api/v4/search/fetch?query=" # + keyword + "&tags=" + filter
    endpoints = {
        "POST": {
            "spawn_machine": "/api/v4/vm/spawn", # POST DATA {"machine_id": id}
            "terminate_machine": "/api/v4/vm/terminate", # POST DATA {"machine_id": id}
            "reset_machine": "/api/v4/vm/reset", # POST DATA {"machine_id": id}
        }
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
    
    active_machine_data = Reactive({})
    
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)        
        self.selected_machine_id: int = 0
        self.selected_machine_data = {}  
        self.border_title = "Machine Details"        
        # self.loading = True

    def compose(self) -> ComposeResult:
        """
        Composes the layout of the application.
        """
        yield Static(id="machine_details")
        with Container(id="machine_control_buttons"):
            yield Button("Spawn Machine", id="spawn_machine_button")
            yield Button("Stop Machine", id="stop_machine_button")
            yield Button("Reset Machine", id="reset_machine_button", variant="default")

    def set_context(self, machine_id: int, machine_data: dict) -> None:
        """
        Selects a machine from the list of current machines.
        """
        self.selected_machine_id = machine_id
        self.selected_machine_data = machine_data
        self.border_title = f"{self.selected_machine_data['name']} :: {self.selected_machine_id}"
        self.styles.border_title_color = "#9fef00"
        self.handle_set_context()

    def handle_set_context(self) -> None:
        
        self.enable_buttons()

        if self.active_machine_data["id"] is not None:
            if int(self.active_machine_data["id"]) == self.selected_machine_id:
                self.add_class("active")                
                self.remove_class("active_but_inactive")
                self.remove_class("inactive")
            else:
                self.remove_class("active")
                self.add_class("active_but_inactive")
                self.remove_class("inactive")
        else:
            self.remove_class("active")
            self.remove_class("active_but_inactive")
            self.add_class("inactive")   
        
        self.query_one(Static).update(self.make_machine_details())
        

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
    
    def has_active_machine(self) -> bool:
        """
        Returns True if there is an active machine, otherwise False.
        """
        return self.active_machine_data["id"] is not None

    def enable_buttons(self) -> None:
        """
        Enables the machine control buttons.
        """
        buttons = self.query(Button)
        for button in buttons:
            button.disabled = False

    def disable_buttons(self) -> None:
        """
        Disables the machine control buttons.
        """
        buttons = self.query(Button)
        for button in buttons:
            button.disabled = True

    def make_machine_details(self) -> None:
        """
        Makes the machine details.
        """
        table = Table.grid(expand=True)
        table.add_column(justify="justify")
        table.add_column(justify="justify")

        """
        Example data:

        "id": machine["id"],
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

        # table.add_row(f"[#9fef00]{self.selected_machine_data["name"]}[/#9fef00] :: [#9fef00]{self.selected_machine_id}")
        table.add_row(
            self.selected_machine_data["os"], 
            f"[{self.machine_difficulty_map[self.selected_machine_data['difficulty']]}]{self.selected_machine_data["difficulty"]}"
        )
        table.add_row(
            "User Flag ✅" if self.selected_machine_data['user_owned'] else "User Flag ❌",
            "Root Flag ✅" if self.selected_machine_data['root_owned'] else "Root Flag ❌"
        )
        table.add_row(
            f"{self.selected_machine_data["points"]} points",
            f"{self.selected_machine_data["rating"]} stars"
        )

        # table.add_row(
        #     "Active" if self.selected_machine_data["active"] else "Inactive",
        #     "Competitive" if self.selected_machine_data["is_competitive"] else "Non-Competitive"
        # )

        # table.add_row("Labels", self.selected_data["labels"])
        # table.add_row("Feedback", self.selected_data["feedbackForChart"])
            
        table.add_row("User Owns", str(self.selected_machine_data["user_owns_count"]))
        table.add_row("Root Owns", str(self.selected_machine_data["root_owns_count"]))

        # convert release date string to human readable format
        release_date = datetime.strptime(self.selected_machine_data["release"], "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%B %d, %Y")
        table.add_row("Release", release_date)

        return table
    
    @on(DataReceived)
    def handle_data_received(self, message: DataReceived) -> None:
        """
        Handles the data received event.

        Args:
            message (DataReceived): The data received message.

        Returns:
            None
        """
        self.app.post_message(LogMessage(f"[+] Data received: {message.key}"))
        self.active_machine_data = message.data
        self.set_context(self.active_machine_data["id"], self.active_machine_data)

    @on(Button.Pressed, selector="#spawn_machine_button")
    async def spawn_button_pressed(self) -> None:
        """
        Event handler for when the spawn machine button is pressed.
        """
        self.disable_buttons()
        id : int = self.selected_machine_id
        started = await self.start_machine(id)
        if started:
            self.app.post_message(LogMessage(f"[+] Machine started"))
        self.enable_buttons()

    async def start_machine(self, machine_id: int) -> bool:
        """
        Starts a machine with the specified machine ID.

        Args:
            machine_id (int): The ID of the machine to start.

        Returns:
            None
        """
        self.app.post_message(LogMessage(f"[+] Starting machine with id: {machine_id}"))
        data = await self.spawn_machine(machine_id)
        if "message" in data:
            self.app.post_message(DebugMessage({f"[!] {data['message']}"}, DebugLevel.LOW))

            if "deployed" in data["message"]:
                # self.active_machine_id = machine_id
                self.app.post_message(LogMessage(f"[+] Active machine ID: {machine_id}"))
                
                return True
            else:
                return False

    @on(Button.Pressed, selector="#stop_machine_button")
    async def stop_button_pressed(self) -> None:
        """
        Event handler for when the stop machine button is pressed.
        """
        self.disable_buttons()
        stopped = await self.stop_machine()
        if stopped:
            self.app.post_message(LogMessage(f"[+] Machine stopped"))
        self.enable_buttons()          

    async def stop_machine(self) -> bool:
        """
        Stops the active machine.

        If there is no active machine, it logs a message and returns.
        Otherwise, it retrieves the machine ID of the active machine,
        stops the machine, and logs the result.

        Returns:
            None
        """
        machine_id = self.selected_machine_id
        self.app.post_message(LogMessage(f"[-] Stopping machine with id: {machine_id}"))
        data = await self.terminate_machine(machine_id)
        if "message" in data:
            self.app.post_message(DebugMessage({f"[!] {data['message']}"}, DebugLevel.LOW))

            if "terminated" in data["message"]:
                # self.active_machine_id = None

                return True
            
            else:
                return False

    @on(Button.Pressed, selector="#reset_machine_button")
    async def reset_button_pressed(self) -> None:
        """
        Event handler for when the reset machine button is pressed.
        """
        self.disable_buttons()
        self.app.post_message(LogMessage(f"[-] Restting machine with id: {self.selected_machine_id}"))
        data = await self.reset_machine()
        if data:
            self.app.post_message(DebugMessage({f"[!] {data['message']}"}, DebugLevel.LOW))
        self.enable_buttons()
        self.app.post_message(LogMessage(f"[+] Machine reset"))

    async def reset_machine(self) -> None:
        """
        Resets the active machine.

        This method resets the active machine by calling the `reset_machine` function from the `htb` module.
        If there is no active machine, it logs a message indicating that there is no active machine.

        Returns:
            None
        """
        machine_id = self.selected_machine_id
        
        data = await self.respawn_machine(machine_id)
        if "message" in data:
            self.app.post_message(DebugMessage({f"[!] {data['message']}"}, DebugLevel.LOW))


    async def spawn_machine(self, machine_id: int):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.base_url + self.endpoints["POST"]["spawn_machine"], headers=self.headers, data={"machine_id": machine_id})
                data = response.json()
                
                return data
        except Exception as e:
            return f"Error: {e}"
        
    
    async def terminate_machine(self, machine_id: int):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.base_url + self.endpoints["POST"]["terminate_machine"], headers=self.headers, data={"machine_id": machine_id})
                data = response.json()
                
                return data                
        except Exception as e:
            return f"Error: {e}"
        

    async def respawn_machine(self, machine_id: int):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.base_url + self.endpoints["POST"]["reset_machine"], headers=self.headers, data={"machine_id": machine_id})
                data = response.json()
                
                return data                
        except Exception as e:
            return f"Error: {e}"