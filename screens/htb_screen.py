from textual import on
from textual.screen import Screen
from textual.widgets import Header, Footer, ContentSwitcher, Button, TabbedContent, TabPane
from textual.containers import Container, Horizontal
from textual.app import ComposeResult


from widgets.player_stats import PlayerStats
from widgets.current_machines import CurrentMachines
from widgets.vpn_connection import VPNConnection
from widgets.player_activity import PlayerActivity
from widgets.active_machine import ActiveMachine
from widgets.retired_machines import RetiredMachines


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
        with Container(id="machines_container") as machines_container:
            machines_container.border_title = "Machines"
            with TabbedContent(id="machines_tabbed_content"):
                with TabPane("Current Machines", id="current_machines_tab"):
                    with Container(id="current_machines_container"):    
                        yield CurrentMachines()
                with TabPane("Retired Machines", id="retired_machines_tab"):
                    with Container(id="retired_machines_container"):
                        yield RetiredMachines()


        with Container(id="bottom_container"):
            yield VPNConnection()
            yield ActiveMachine()

    def on_data_table_row_selected(self, row) -> None:
        """
        Event handler for when a data table row is selected.

        Args:
            row (dict): The row that was selected.
        """
        self.query_one(ActiveMachine).update(f"Selected row: {row.row_key.value} from {row.data_table}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.query_one(ContentSwitcher).current = event.button.id 
        self.query_one("#machines_container").border_title = "Current Machines" if event.button.id == "current_machines" else "Retired Machines"