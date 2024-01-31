from enum import Enum

from textual.screen import Screen
from textual.widgets import Header, RichLog, Input, Static
from textual.containers import Container
from textual.app import ComposeResult
from textual.suggester import SuggestFromList

from rich.table import Table
from rich import box

from htb import HTBClient
from htb import SearchFilter

from widgets.player_stats import PlayerStats
from widgets.current_machines import CurrentMachines
from utilities.ping import Ping
from utilities.api_token import APIToken

class HTBScreen(Screen):

    class DebugLevel(Enum):
        NONE = 0
        LOW = 1
        MEDIUM = 2
        HIGH = 3

    TOKEN_NAME = "HTB_TOKEN"

    DEBUG_LEVEL: DebugLevel = DebugLevel.HIGH
    REFRESH_INTERVAL: int = 10
    PING_INTERVAL: int = 5

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
        self.title = "[spellb00k]::Hack The Box Client::"
        self.htb = HTBClient(APIToken(self.TOKEN_NAME).get_token())

    def compose(self) -> ComposeResult:
        """
        Composes the layout of the application.

        Returns:
            ComposeResult: The composed layout of the application.
        """
        player_stats_widget = PlayerStats()
        player_stats_widget.border_title = "Player Stats"

        # machine_list_widget = Static(id="machine_list", classes="box")
        machine_list_widget = CurrentMachines()
        machine_list_widget.border_title = "Current Machines"

        vpn_widget = Static(id="vpn_connection", classes="box")
        vpn_widget.border_title = "VPN Connection"

        active_machine_widget = Static(id="active_machine", classes="box")
        active_machine_widget.border_title = "Active Machine"

        yield Header(show_clock=True)

        yield Container(
            player_stats_widget,
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


    async def on_mount(self) -> None:
        """
        Event handler for when the screen is mounted.

        This method starts the refresh interval for the player stats and the VPN connection status.
        """
        self.run_worker(self.update_connection())
        self.run_worker(self.update_active_machine())

        self.refresh_connection = self.set_interval(self.REFRESH_INTERVAL, self.update_connection)
        self.refresh_active_machine = self.set_interval(self.REFRESH_INTERVAL, self.update_active_machine)

    def on_shutdown(self) -> None:
        """
        Event handler for when the application is shut down.
        """

        # iterate over all workers and cancel them
        for worker in self.workers:
            worker.stop() 

    def on_input_submitted(self, message: Input.Submitted) -> None:
        """
        Event handler for when an input is submitted.

        Args:
            message (Input.Submitted): The submitted input message.
        """
        # if message.validation_result.is_valid:
        self.run_command(message.value)
        message.control.clear()

    def handle_active_machine(self) -> None:
        """
        Handles the active machine.

        If there is an active machine, it writes the machine details to the log and starts pinging the machine at regular intervals.
        If there is no active machine, it stops pinging the machine (if already started).
        """
        if self.htb.active_machine_data["id"] is not None:
            if self.has_active_machine:
                return
            
            self.has_active_machine = True

            log = self.query_one(RichLog)
            log.write("\n")
            log.write("[+] Active machine found")
            log.write(f"[*] Name: {self.htb.active_machine_data['name']}")
            log.write(f"[*] IP: {self.htb.active_machine_data['ip']}")
            log.write(f"[*] OS: {self.htb.active_machine_data['os']}")
            log.write(f"[*] Difficulty: {self.htb.active_machine_data['difficulty']}")
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
            log.write(f"[+] Pinging {self.htb.active_machine_data['ip']}")

        data = await Ping.ping(self.htb.active_machine_data["ip"], 1)
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
        data = await self.htb.get_connection_status()
        if self.DEBUG_LEVEL == self.DebugLevel.HIGH:
            log = self.query_one(RichLog)
            log.write(data)
        vpn_widget.update(self.htb.make_connection())

    async def update_active_machine(self) -> None:
        """
        Updates the active machine widget with the latest active machine data from self.htb.
        """
        active_machine_widget = self.query_one("#active_machine", Static)        
        data = await self.htb.get_active_machine()
        if self.DEBUG_LEVEL == self.DebugLevel.HIGH:
            log = self.query_one(RichLog)
            log.write(data)
        self.handle_active_machine()
        active_machine_widget.update(self.htb.make_active_machine())

    async def fetch_search_results(self, search_type: SearchFilter, search_term: str) -> None:
        """
        Fetches search results based on the search type and term.

        Args:
            search_type (SearchFilter): The type of search filter.
            search_term (str): The search term.
        """
        log = self.query_one(RichLog)
        log.write(f"[+] Finding {search_type} with name: {search_term} \n") 
        data = await self.htb.get_search_results(search_type, search_term)
        
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
        data = await self.htb.spawn_machine(machine_id)
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
        
        machine_id = self.htb.active_machine_data["id"]
        log.write(f"[-] Stopping machine with id: {machine_id}")
        data = await self.htb.terminate_machine(machine_id)
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

        if self.htb.active_machine_data["id"] is None:
            log.write("[!] No active machine")
            return
        
        machine_id = self.htb.active_machine_data["id"]
        log.write(f"[+] Resetting machine with id: {machine_id}")
        data = await self.htb.reset_machine(machine_id)
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
            # case "exit":
            #     self.exit()
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