from textual import on
from textual.screen import Screen
from textual.widgets import Header, Footer, RichLog, TabbedContent, TabPane
from textual.containers import Container, Horizontal
from textual.app import ComposeResult


from widgets.player_stats import PlayerStats
from widgets.current_machines import CurrentMachines
from widgets.vpn_connection import VPNConnection
from widgets.player_activity import PlayerActivity
from widgets.active_machine import ActiveMachine
from widgets.retired_machines import RetiredMachines
from widgets.machine_control import MachineDetails
from widgets.output_log import OutputLog

from messages.debug_message import DebugMessage
from enums.debug_level import DebugLevel 
from messages.data_received import DataReceived


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
        self.title = ":: HTBtui ::"


    def compose(self) -> ComposeResult:
        """
        Composes the layout of the application.

        Returns:
            ComposeResult: The composed layout of the application.
        """

        yield Header(show_clock=True)

        with Container(id="player_container"):
            with Container(id="player_stats_container") as player_stats_container:
                player_stats_container.border_title = "Player Stats"
                yield PlayerStats()
            with Container(id="player_activity_container") as player_activity_container:
                player_activity_container.border_title = "Player Activity"
                yield PlayerActivity()
        with Container(id="machines"):
            with Container(id="machines_container") as machines_container:
                machines_container.border_title = "Machines"
                with TabbedContent(id="machines_tabbed_content"):
                    with TabPane("Current Machines", id="current_machines_tab"):
                        with Container(id="current_machines_container"):    
                            yield CurrentMachines()
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
    
    @on(DataReceived)
    def handle_data_received(self, message: DataReceived) -> None:
        """
        Handles the data received event.

        Args:
            message (DataReceived): The data received message.

        Returns:
            None
        """
        machine_details = self.query_one(MachineDetails)
        machine_details.active_machine_data = message.data
        self.post_message(DebugMessage({"Active Machine Data": message.data}, DebugLevel.LOW))
        if message.key == "active_machine" and machine_details.has_active_machine():
            id = message.data["id"]
            machine_details.set_context(id, message.data)