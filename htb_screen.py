import os

from enum import Enum

from textual import on
from textual.app import App, ComposeResult
from textual.widgets import RichLog, Static, Input, Footer, Header, Sparkline
from textual.containers import Container
from textual.suggester import SuggestFromList

from rich.table import Table, box
from rich.markdown import Markdown

from htb import HTBClient, SearchFilter
from utilities.ping import Ping
from utilities.api_token import APIToken
from widgets.current_machines import CurrentMachines

KEY_NAME = "HTB_TOKEN"
KEY = APIToken(KEY_NAME).get_token()

htb = HTBClient(KEY)    

# markdown test
MARKDOWN = """
# This is an h1

Rich can do a pretty *decent* job of rendering markdown.

1. This is a list item
2. This is another list item
"""

class spellb00k(App):
    """
    The spellb00k class represents the main application for the spellb00k program.
    It inherits from the `App` class provided by the `textual.app` module.

    Attributes:
        DebugLevel (Enum): An enumeration representing the debug levels.
        CSS_PATH (str): The path to the CSS file.
        DEBUG_LEVEL (DebugLevel): The current debug level.
        REFRESH_INTERVAL (int): The interval (in seconds) for refreshing the widgets.
        PING_INTERVAL (int): The interval (in seconds) for pinging the active machine.
        valid_base_commands (list): A list of valid base commands.
        command_tree (dict): A dictionary representing the command tree.
        ping (None): Placeholder for the ping object.

    Methods:
        compose(): Composes the layout of the application.
        on_load(): Event handler for when the application is loaded.
        on_ready(): Event handler for when the application is ready.
        on_mount(): Event handler for when the application is mounted.
        on_input_submitted(message: Input.Submitted): Event handler for when an input is submitted.
        on_shutdown(): Event handler for when the application is shut down.
        handle_active_machine(): Handles the active machine.
        ping_host(host: str, count: int): Pings the specified host a given number of times.
        ping_active_machine(): Pings the active machine and updates the ping widget.
        update_connection(): Updates the VPN connection status and widget.
        update_profile(): Updates the player's profile widget.
        update_season(): Updates the season widget.
        update_machine_list(): Updates the machine list widget.
        update_active_machine(): Updates the active machine widget.
        fetch_search_results(search_type: SearchFilter, search_term: str): Fetches search results based on the search type and term.
    """
    class DebugLevel(Enum):
        NONE = 0
        LOW = 1
        MEDIUM = 2
        HIGH = 3

    CSS_PATH = "htb.tcss"
    DEBUG_LEVEL: DebugLevel = DebugLevel.NONE
    REFRESH_INTERVAL: int = 10
    PING_INTERVAL: int = 5

    valid_base_commands = ["help",
                           "exit",
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
        "exit" : [],
    }
    ping = None

    def compose(self) -> ComposeResult:
        """
        Composes the layout of the application.

        Returns:
            ComposeResult: The composed layout of the application.
        """
        stats_widget = Container(
                Static(id="player"),
                Static(id="season"),
                id="stats_container"
            )
        stats_widget.border_title = "Player Stats"

        # machine_list_widget = Static(id="machine_list", classes="box")
        machine_list_widget = CurrentMachines()
        machine_list_widget.border_title = "Current Machines"

        vpn_widget = Static(id="vpn_connection", classes="box")
        vpn_widget.border_title = "VPN Connection"

        active_machine_widget = Static(id="active_machine", classes="box")
        active_machine_widget.border_title = "Active Machine"

        yield Header(
            "spellb00k",
        )

        yield Container(
            stats_widget,
            machine_list_widget,
            id="sidebar",
            classes="box"
        )
        yield Container(
            RichLog(highlight=True, markup=True, auto_scroll=True, wrap=True, min_width=90, id="console"),
            Input(
                placeholder="Enter a command",
                suggester=SuggestFromList(self.valid_base_commands, case_sensitive=True),
                # validators=[Function(self.is_valid_command, "Invalid command")],
                id="input"
            ),
            classes="box",
            id="main"
        )
        yield Container(
            vpn_widget,
            classes="box",
            id="footer_left"
        )
        yield Container(
            active_machine_widget,
            Static(id="ping"),
            classes="box",
            id="footer_right"
        )

    def on_load(self) -> None:
        """
        Event handler for when the application is loaded.
        """
        self.refresh_connection = None
        self.refresh_active_machine = None
        self.refresh_active_machine_ping = None
        self.has_active_machine = False

    def on_ready(self) -> None:
        """
        Event handler for when the application is ready.
        """
        log = self.query_one(RichLog)
        log.write("[bold purple]Welcome to spellb00k!")

        # testing markdown support
        md = Markdown(MARKDOWN)
        log.write(md)

    async def on_mount(self) -> None:
        """
        Event handler for when the application is mounted.
        """
        # Run the workers
        self.run_worker(self.update_connection())
        self.run_worker(self.update_profile())
        self.run_worker(self.update_season())
        # self.run_worker(self.update_machine_list())
        self.run_worker(self.update_active_machine())

        # self.run_worker(self.ping_host("1.1.1.1", 1))        

        # Refresh widgets every {self.REFRESH_INTERVAL} seconds
        self.refresh_connection = self.set_interval(self.REFRESH_INTERVAL, self.update_connection)
        self.refresh_active_machine = self.set_interval(self.REFRESH_INTERVAL, self.update_active_machine)

    def on_input_submitted(self, message: Input.Submitted) -> None:
        """
        Event handler for when an input is submitted.

        Args:
            message (Input.Submitted): The submitted input message.
        """
        # if message.validation_result.is_valid:
        self.run_command(message.value)
        message.control.clear()

    def on_shutdown(self) -> None:
        """
        Event handler for when the application is shut down.
        """

        # iterate over all workers and cancel them
        for worker in self.workers:
            worker.stop() 

    def handle_active_machine(self) -> None:
        """
        Handles the active machine.

        If there is an active machine, it writes the machine details to the log and starts pinging the machine at regular intervals.
        If there is no active machine, it stops pinging the machine (if already started).
        """
        if htb.active_machine_data["id"] is not None:
            if self.has_active_machine:
                return
            
            self.has_active_machine = True

            log = self.query_one(RichLog)
            log.write("\n")
            log.write("[+] Active machine found")
            log.write(f"[*] Name: {htb.active_machine_data['name']}")
            log.write(f"[*] IP: {htb.active_machine_data['ip']}")
            log.write(f"[*] OS: {htb.active_machine_data['os']}")
            log.write(f"[*] Difficulty: {htb.active_machine_data['difficulty']}")
            log.write("\n")

            self.refresh_active_machine_ping = self.set_interval(
                self.PING_INTERVAL,
                self.ping_active_machine
                )
        else:
            self.has_active_machine = False
            if self.refresh_active_machine_ping is not None:
                self.refresh_active_machine_ping.stop()

    async def ping_host(self, host: str, count: int) -> None:
        """
        Ping the specified host a given number of times.

        Args:
            host (str): The IP address or hostname to ping.
            count (int): The number of times to ping the host.
        """
        if self.DEBUG_LEVEL.value >= self.DebugLevel.LOW.value:
            log = self.query_one(RichLog)
            log.write(f"[+] Pinging {host}")
        
        data = await Ping.ping(host, count)

        if self.DEBUG_LEVEL.value >= self.DebugLevel.LOW.value:
            log.write(f"{data}")

    async def ping_active_machine(self) -> None:
        """
        Ping the active machine and update the ping widget with the result.

        Raises:
            Exception: If there is an error while pinging the machine.
        """
        if self.DEBUG_LEVEL.value >= self.DebugLevel.LOW.value:
            log = self.query_one(RichLog)
            log.write(f"[+] Pinging {htb.active_machine_data['ip']}")

        data = await Ping.ping(htb.active_machine_data["ip"], 1)
        try:
            data = data.split('\n')[-1].split('=')[-1].split()[0].split('/')[1].split('.')[0]
            ping_widget = self.query_one("#ping", Static)
            ping_widget.update(data + "ms")
        except Exception as e:
            data = "Error: " + str(e)

        if self.DEBUG_LEVEL.value >= self.DebugLevel.LOW.value:
            log.write(f"[+] {data.split('\n')[-1].split('=')[-1].split()[0].split('/')[1].split('.')[0]}ms")

    async def update_connection(self) -> None:
        """
        Updates the VPN connection status and updates the VPN widget accordingly.
        """
        vpn_widget = self.query_one("#vpn_connection", Static)        
        data = await htb.get_connection_status()
        if self.DEBUG_LEVEL == self.DebugLevel.HIGH:
            log = self.query_one(RichLog)
            log.write(data)
        vpn_widget.update(htb.make_connection())

    async def update_profile(self) -> None:
        """
        Updates the player's profile widget with the latest data from Hack The Box API.

        This method retrieves the player's profile data using the `htb.get_profile()` function,
        and then updates the player widget with the newly fetched data using the `update()` method
        of the player_widget.

        If the DEBUG_LEVEL is set to `DebugLevel.HIGH`, the retrieved profile data is also logged
        using the `RichLog` widget.
        """
        player_widget = self.query_one("#player", Static)        
        data = await htb.get_profile()
        if self.DEBUG_LEVEL == self.DebugLevel.HIGH:
            log = self.query_one(RichLog)
            log.write(data)
        player_widget.update(htb.make_profile())

    async def update_season(self) -> None:
        """
        Updates the season widget with the latest season data from HTB.
        """
        season_widget = self.query_one("#season", Static)        
        data = await htb.get_season_data()
        if self.DEBUG_LEVEL == self.DebugLevel.HIGH:
            log = self.query_one(RichLog)
            log.write(data)
        season_widget.update(htb.make_season())

    async def update_machine_list(self) -> None:
        """
        Updates the machine list widget with the latest machine list data from HTB.
        """
        machine_list_widget = self.query_one(CurrentMachines)        
        data = await htb.get_machine_list()
        if self.DEBUG_LEVEL == self.DebugLevel.HIGH:
            log = self.query_one(RichLog)
            log.write(data)
        machine_list_widget.update(htb.make_machine_list())

    async def update_active_machine(self) -> None:
        """
        Updates the active machine widget with the latest active machine data from HTB.
        """
        active_machine_widget = self.query_one("#active_machine", Static)        
        data = await htb.get_active_machine()
        if self.DEBUG_LEVEL == self.DebugLevel.HIGH:
            log = self.query_one(RichLog)
            log.write(data)
        self.handle_active_machine()
        active_machine_widget.update(htb.make_active_machine())

    async def fetch_search_results(self, search_type: SearchFilter, search_term: str) -> None:
        """
        Fetches search results based on the search type and term.

        Args:
            search_type (SearchFilter): The type of search filter.
            search_term (str): The search term.
        """
        log = self.query_one(RichLog)
        log.write(f"[+] Finding {search_type} with name: {search_term} \n") 
        data = await htb.get_search_results(search_type, search_term)
        
        table = Table(expand=True, box=box.ASCII)
        table.add_column("#")
        table.add_column("id", no_wrap=True)
        table.add_column("name")

        try:
            # sometimes the data is a dict, sometimes it's a list ::shrug::
            if isinstance(data[search_type], dict):
                for i, result in enumerate(data[search_type].values()):
                    table.add_row(str(i), result["id"], result["value"])
            else:
                for i, result in enumerate(data[search_type]):
                    table.add_row(str(i), result["id"], result["value"])

            log.write(table)
            log.write("\n")
            log.write(f"[*] Found {len(data[search_type])} {search_type} with name: {search_term}")
            log.write(f"[*] Use the id to start the machine with: start <id>")
        except Exception as e:
            log.write(f"Error: {str(e)}")
            log.write(f"[!] Error: {e}")


    async def start_machine(self, machine_id: int) -> None:
        """
        Starts a machine with the specified machine ID.

        Args:
            machine_id (int): The ID of the machine to start.

        Returns:
            None
        """
        log = self.query_one(RichLog)
        log.write(f"[+] Starting machine with id: {machine_id}")
        data = await htb.spawn_machine(machine_id)
        if "message" in data:
            log.write("[!] " + data["message"])

            if "deployed" in data["message"]:
                log.write("[+] Active machine updated")


    async def stop_machine(self) -> None:
        """
        Stops the active machine.

        If there is no active machine, it logs a message and returns.
        Otherwise, it retrieves the machine ID of the active machine,
        stops the machine, and logs the result.

        Returns:
            None
        """
        log = self.query_one(RichLog)

        if not self.has_active_machine:
            log.write("[!] No active machine")
            return
        
        machine_id = htb.active_machine_data["id"]
        log.write(f"[-] Stopping machine with id: {machine_id}")
        data = await htb.terminate_machine(machine_id)
        if "message" in data:
            log.write("[!] " + data["message"])


    async def reset_machine(self) -> None:
        """
        Resets the active machine.

        This method resets the active machine by calling the `reset_machine` function from the `htb` module.
        If there is no active machine, it logs a message indicating that there is no active machine.

        Returns:
            None
        """
        log = self.query_one(RichLog)

        if htb.active_machine_data["id"] is None:
            log.write("[!] No active machine")
            return
        
        machine_id = htb.active_machine_data["id"]
        log.write(f"[+] Resetting machine with id: {machine_id}")
        data = await htb.reset_machine(machine_id)
        log.write("[!] " + data["message"])
        
    def run_command(self, command: str) -> None:
        """
        Executes the specified command.

        Args:
            command (str): The command to be executed.

        Returns:
            None
        """
        log = self.query_one(RichLog)
        
        cmds = command.split()

        match cmds[0]:
            case "help":
                log.write("help")
            case "exit":
                self.exit()
            case "clear":
                log.clear()
            case "reset":
                if len(cmds) > 1:
                    log.write("Usage: reset")
                else:
                    self.run_worker(self.reset_machine())
            case "start":
                if len(cmds) != 2:
                    log.write("Usage: start <machine_id>")
                else:
                    self.run_worker(self.start_machine(int(cmds[1])))
            case "stop":
                if len(cmds) > 1:
                    log.write("Usage: stop")
                else:
                    self.run_worker(self.stop_machine())
            case "refresh":
                log.write("refresh")
            case "find":
                if len(cmds) < 3 or len(cmds) > 3:
                    log.write("Usage: find <machines|users> <name>")
                else:                     
                    self.run_worker(self.fetch_search_results(cmds[1], cmds[2]))                  
            case _:
                log.write("[red]Invalid command")


if __name__ == "__main__":
    app = spellb00k()
    app.run()
    
    