import httpx
from datetime import datetime
from textual import on
from textual.app import ComposeResult
from textual.widgets import Static, Button, Sparkline, Label, Rule
from textual.containers import Container
from textual.reactive import Reactive

from rich.table import Table

from utilities import APIToken
from enums import DebugLevel
from messages import DebugMessage, LogMessage


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

    """
    {
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
    """
    
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)        
        self.selected_machine_id: int = 0
        self.selected_machine_data = {}  
        self.border_title = "Machine Info" 
        
        # self.loading = True

    def compose(self) -> ComposeResult:
        """
        Composes the layout of the application.
        """
        yield Static(id="machine_details")
        with Container(id="machine_feedback_container"):
            yield Rule()        
            with Container(id="feedback_container"):
                yield Sparkline(id="feedback_sparkline_easy")
                yield Sparkline(id="feedback_sparkline_medium")
                yield Sparkline(id="feedback_sparkline_hard")
            yield Label("User Rated Difficulty")
            yield Rule()
        with Container(id="machine_control_buttons"):
            yield Button("Spawn Machine", id="spawn_machine_button")
            yield Button("Stop Machine", id="stop_machine_button", variant="error")
            yield Button("Reset Machine", id="reset_machine_button", variant="default")

    def set_context(self, machine_id: int, machine_data: dict) -> None:
        """
        Selects a machine from the list of current machines.
        """
        self.selected_machine_id = machine_id
        self.selected_machine_data = machine_data
        self.border_title = f"{self.selected_machine_data['name']}::{self.selected_machine_id}"
        self.handle_display_buttons()
        self.query_one("#machine_details").update(self.make_machine_details())    

    def clear_context(self) -> None:
        """
        Clears the selected machine context.
        """
        self.app.post_message(LogMessage(f"[-] Clearing machine context"))
        self.selected_machine_id = None
        self.selected_machine_data = {}
        self.border_title = "Machine Info"
        self.handle_display_buttons()
        self.query_one("#machine_details").update("")        

    def get_context(self) -> dict:
        """
        Returns the selected machine context.
        """
        return self.selected_machine_data
    
    def has_active_machine(self) -> bool:
        """
        Returns True if there is an active machine, otherwise False.
        """
        return self.active_machine_data
    
    def watch_active_machine_data(self, old_value, new_value) -> None:
        """
        Watches the active machine data for changes.
        """
        self.app.post_message(LogMessage(f"[+] Active machine data changed from: {old_value} to: {new_value}"))
        if self.has_active_machine():
            id = new_value["id"]
            self.set_context(id, new_value)
        else:
            self.clear_context()

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

    def handle_display_buttons(self) -> None:
        
        self.enable_buttons()

        if self.has_active_machine():
            self.add_class("active")
            self.remove_class("inactive")
        elif self.selected_machine_id is not None:
            self.remove_class("active")
            self.add_class("inactive")
        else:
            self.remove_class("active")
            self.remove_class("inactive")

    def make_feedback_sparkline(self) -> None:
        """
        Makes the feedback sparkline.
        """
        feedback = self.selected_machine_data["feedbackForChart"]
        feedback_data = []
        for key, value in feedback.items():
            feedback_data.append(value)
        
        self.query_one("#feedback_sparkline_easy").data = feedback_data[slice(3)]
        self.query_one("#feedback_sparkline_medium").data = feedback_data[slice(3, 6)]
        self.query_one("#feedback_sparkline_hard").data = feedback_data[slice(7, 10)]


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
            
        table.add_row("User Owns", str(self.selected_machine_data["user_owns_count"]))
        table.add_row("Root Owns", str(self.selected_machine_data["root_owns_count"]))

        # convert release date string to human readable format
        release_date = datetime.strptime(self.selected_machine_data["release"], "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%B %d, %Y")
        table.add_row("Release", release_date)

        self.make_feedback_sparkline()

        return table

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