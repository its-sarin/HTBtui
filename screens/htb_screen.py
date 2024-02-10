from textual import on
from textual.screen import Screen
from textual.widgets import Header, TabbedContent, TabPane, Rule
from textual.containers import Container
from textual.app import ComposeResult

from widgets import PlayerStats, CurrentMachines, RetiredMachines, SeasonalMachines, VPNConnection, PlayerActivity, ActiveMachine, MachineDetails, OutputLog
from messages import DebugMessage, DataReceived
from enums import DebugLevel 


class HTBScreen(Screen):    

    TOKEN_NAME = "HTB_TOKEN"

    valid_base_commands = ["help",
                        # "exit",
                        "clear",
                        "reset",
                        "start",
                        "stop",
                        "reset",
                        "refresh",
                        "find",
                        "find users",
                        "find machines"
                        ]
    command_tree = {
        "find" : [
            "machines",
            "users"
        ],
        "clear" : [],
        "start" : [],
        "stop" : [],
        "reset" : [],
        # "exit" : [],
    }

    CSS_PATH = "htb_screen.tcss"    

    
    def __init__(self) -> None:
        super().__init__()
        self.refresh_active_machine_ping = None
        self.has_active_machine = False
        self.active_machine_data = {}
        self.title = "::HTBtui::"


    def compose(self) -> ComposeResult:
        """
        Composes the layout of the application.

        Returns:
            ComposeResult: The composed layout of the application.
        """

        yield Header(show_clock=True)

        with Container(id="player_information_container"):
            yield PlayerStats(id="player_stats")
            yield PlayerActivity(id="player_activity")
        yield Rule(classes="app_rule")
        with Container(id="machines"):
            with Container(id="machines_container") as machines_container:
                machines_container.border_title = "Machines"
                with TabbedContent(id="machines_tabbed_content"):                    
                    with TabPane("Current Machines", id="current_machines_tab"):
                        with Container(id="current_machines_container"):    
                            yield CurrentMachines()                    
                    with TabPane("Seasonal Machines", id="seasonal_machines_tab"):
                        with Container(id="seasonal_machines_container"):
                            yield SeasonalMachines()
                    with TabPane("Retired Machines", id="retired_machines_tab"):
                        with Container(id="retired_machines_container"):
                            yield RetiredMachines()
            yield MachineDetails(id="machine_control")
        yield OutputLog(id="log")
        with Container(id="bottom_container"):
            yield VPNConnection()
            yield ActiveMachine(id="active_machine")
    
    def on_data_table_row_selected(self, event) -> None:
        """
        Handles the event when a row is selected in the data table.

        Args:
            event: The event object containing information about the selected row.

        Returns:
            None
        """
        if event.control.id == "current_machines" or event.control.id == "retired_machines":
            machine_details = self.query_one(MachineDetails)
            if not machine_details.has_active_machine():
                machine_details.set_context(event.row_key.value, event.control.machine_data[int(event.row_key.value)])

        if event.control.id == "seasonal_machines":
            self.post_message(DebugMessage({"Seasonal Machines": event}, DebugLevel.LOW))
            machine_details = self.query_one(MachineDetails)
            if not machine_details.has_active_machine():
                if event.row_key.value in event.control.active_ids:
                    machine_details.set_context(event.row_key.value, self.query_one("#current_machines").machine_data[int(event.row_key.value)])
                else:
                    machine_details.clear_context()
    
    @on(DataReceived)
    def handle_data_received(self, message: DataReceived) -> None:
        """
        Handles the data received event.

        Args:
            message (DataReceived): The data received message.

        Returns:
            None
        """
        try:
            machine_details = self.query_one(MachineDetails)
            if message.key == "active_machine":
                if isinstance(message.data, dict) and "id" in message.data:
                    machine_details.active_machine_data = message.data if message.data["id"] else {}

            self.post_message(DebugMessage({"[!] Active Machine Data": message.data}, DebugLevel.HIGH))
        except Exception as e:
            self.post_message(DebugMessage({"Error": e}, DebugLevel.MEDIUM))