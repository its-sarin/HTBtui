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
from widgets.machine_control import MachineControl


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
            with Container(id="machine_control_container"):
                yield MachineControl()
                yield Button("Spawn Machine")


        with Container(id="bottom_container"):
            yield VPNConnection()
            yield ActiveMachine()

    def on_data_table_row_selected(self, event) -> None:
        if event.control.id == "current_machines" or event.control.id == "retired_machines":
            # self.query_one(ActiveMachine).update(f"Selected row: {event.row_key.value} from {event.data_table}")
            # self.query_one(PlayerStats).update(f"{event.control.id}:{event.control.machine_data[int(event.row_key.value)]}")

            self.query_one(MachineControl).set_context(event.row_key.value, event.control.machine_data[int(event.row_key.value)])
    # @on(PlayerActivity.RowSelected)
    # def handle_activity_row_selected(self, event: PlayerActivity.RowSelected) -> None:
    #     self.query_one(ActiveMachine).update(f"Selected row: {event.row_key.value} from {event.data_table}")

    # def on_data_table_row_selected(self, row) -> None:
    #     """
    #     Event handler for when a data table row is selected.

    #     Args:
    #         row (dict): The row that was selected.
    #     """
    #     self.query_one(ActiveMachine).update(f"Selected row: {row.row_key.value} from {row.data_table}")
    #     # if row.control.machine_data:
    #         # self.query_one(ActiveMachine).update(f"{row.data_table}:{row.control.machine_data[int(row.row_key.value)]}")
    #     self.query_one(PlayerStats).update(f"{row}:{row.control.machine_data[int(row.row_key.value)]}")

    