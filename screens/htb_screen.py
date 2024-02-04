from textual import on
from textual.screen import Screen
from textual.widgets import Header, Footer, ContentSwitcher, Button
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
        player_stats_widget = PlayerStats()
        player_stats_widget.border_title = "Player Stats"

        player_activity_widget = PlayerActivity()
        player_activity_widget.border_title = "Player Activity"

        current_machines_widget = CurrentMachines()
        current_machines_widget.border_title = "Current Machines"
        current_machines_widget.id = "current_machines"

        retired_machines_widget = RetiredMachines()
        retired_machines_widget.border_title = "Retired Machines"
        retired_machines_widget.id = "retired_machines"

        vpn_widget = VPNConnection()
        vpn_widget.border_title = "VPN Connection"

        active_machine_widget = ActiveMachine()
        active_machine_widget.border_title = "Active Machine"

        yield Header(show_clock=True)

        with Horizontal(id="player_container"):
            with Container(id="player_stats_container") as player_stats_container:
                player_stats_container.border_title = "Player Stats"
                yield player_stats_widget
            with Container(id="player_activity_container"):
                yield player_activity_widget
        with Container(id="machines_container"):
            with Horizontal(id="buttons"):  
                yield Button("Current Machines", id="current_machines")  
                yield Button("Retired Machines", id="retired_machines") 
            with ContentSwitcher(id="machines_switcher", initial="current_machines"):
                with Container(id="current_machines"):
                    yield current_machines_widget
                with Container(id="retired_machines"):
                    yield retired_machines_widget

        with Horizontal(id="bottom_container"):
            yield Container(
                vpn_widget,
                classes="box",
                id="connection_container"
            )
            yield Container(
                active_machine_widget,
                classes="box",
                id="active_machine_container"
            )
        yield Footer()

    def on_data_table_row_selected(self, row) -> None:
        """
        Event handler for when a data table row is selected.

        Args:
            row (dict): The row that was selected.
        """
        self.query_one(ActiveMachine).update(f"Selected row: {row.row_key.value} from {row.data_table}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.query_one(ContentSwitcher).current = event.button.id 