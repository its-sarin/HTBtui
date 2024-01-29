import os

from textual import on
from textual.app import App, ComposeResult
from textual.widgets import RichLog, Static, Input, Footer, Header
from textual.containers import Container
from textual.validation import Function, Number, ValidationResult, Validator
from textual.suggester import SuggestFromList

from rich.table import Table, box

from htb import HTBClient, SearchFilter

# get api key from environment variable and throw error if not found
ENV_NAME = "HTB_API_KEY"
API_KEY = os.environ[ENV_NAME] if ENV_NAME in os.environ else None
if API_KEY is None:
    raise Exception(f"Environment variable {ENV_NAME} not found")
elif len(API_KEY.split('.')) != 3:
    raise Exception(f"Invalid API key found in {ENV_NAME}. Please check your API key or generate a new one.")

htb = HTBClient(API_KEY)    

class spellb00k(App):
    CSS_PATH = "htb.tcss"
    DEBUG = False
    REFRESH_INTERVAL = 10

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
    }

    def compose(self) -> ComposeResult:
        stats_widget = Container(
                Static(id="player"),
                Static(id="season"),
                id="stats_container"
            )
        stats_widget.border_title = "Player Stats"

        machine_list_widget = Static(id="machine_list")
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
            classes="box",
            id="footer_right"
        )

    def on_ready(self) -> None:
        log = self.query_one(RichLog)
        log.write("[bold purple]Welcome to spellb00k!")

    def on_shutdown(self) -> None:
        self.refresh_connection.cancel()
        self.refresh_active_machine.cancel()    

    async def on_mount(self) -> None:
        # Run the workers
        self.run_worker(self.update_connection())
        self.run_worker(self.update_profile())
        self.run_worker(self.update_season())
        self.run_worker(self.update_machine_list())
        self.run_worker(self.update_active_machine())

        # Refresh widgets every {self.REFRESH_INTERVAL} seconds
        self.refresh_connection = self.set_interval(self.REFRESH_INTERVAL, self.update_connection)
        self.refresh_active_machine = self.set_interval(self.REFRESH_INTERVAL, self.update_active_machine)

    def on_input_submitted(self, message: Input.Submitted) -> None:
        # if message.validation_result.is_valid:
        self.run_command(message.value)
        message.control.clear()
        
    async def update_connection(self) -> None:
        vpn_widget = self.query_one("#vpn_connection", Static)
        log = self.query_one(RichLog)
        data = await htb.get_connection_status()
        if self.DEBUG:
            log.write(data)
        vpn_widget.update(htb.make_connection())

    async def update_profile(self) -> None:
        player_widget = self.query_one("#player", Static)
        log = self.query_one(RichLog)
        data = await htb.get_profile()
        if self.DEBUG:
            log.write(data)
        player_widget.update(htb.make_profile())

    async def update_season(self) -> None:
        season_widget = self.query_one("#season", Static)
        log = self.query_one(RichLog)
        data = await htb.get_season_data()
        if self.DEBUG:
            log.write(data)
        season_widget.update(htb.make_season())

    async def update_machine_list(self) -> None:
        machine_list_widget = self.query_one("#machine_list", Static)
        log = self.query_one(RichLog)
        data = await htb.get_machine_list()
        if self.DEBUG:
            log.write(data)
        machine_list_widget.update(htb.make_machine_list())

    async def update_active_machine(self) -> None:
        active_machine_widget = self.query_one("#active_machine", Static)
        log = self.query_one(RichLog)
        data = await htb.get_active_machine()
        if self.DEBUG:
            log.write(data)
        active_machine_widget.update(htb.make_active_machine())

    async def fetch_search_results(self, search_type: SearchFilter, search_term: str) -> None:
        log = self.query_one(RichLog)
        log.write(f"[*] Finding {search_type} with name: {search_term} \n") 
        data = await htb.get_search_results(search_type, search_term)

        try:
            table = Table(expand=True, box=box.ASCII)
            table.add_column("#")
            table.add_column("id", no_wrap=True)
            table.add_column("name")

            # sometimes the data is a dict, sometimes it's a list ::shrug::
            if isinstance(data[search_type], dict):
                for i, result in enumerate(data[search_type].values()):
                    table.add_row(str(i), result["id"], result["value"])
            else:
                for i, result in enumerate(data[search_type]):
                    table.add_row(str(i), result["id"], result["value"])

            log.write(table)
            log.write("\n")
            log.write(f"[+] Found {len(data[search_type])} {search_type} with name: {search_term}")
            log.write(f"[+] Use the id to start the machine with: start <id>")
        except Exception as e:
            log.write(f"[red]{e}")


    async def start_machine(self, machine_id: int) -> None:
        log = self.query_one(RichLog)
        log.write(f"[*] Starting machine with id: {machine_id}")
        data = await htb.spawn_machine(machine_id)
        log.write("[!] " + data["message"])

    async def stop_machine(self) -> None:
        log = self.query_one(RichLog)

        if htb.active_machine_data["id"] is None:
            log.write("[!] No active machine")
            return
        
        machine_id = htb.active_machine_data["id"]
        log.write(f"[*] Stopping machine with id: {machine_id}")
        data = await htb.terminate_machine(machine_id)
        log.write("[!] " + data["message"])
        
    def run_command(self, command: str) -> None:
        log = self.query_one(RichLog)
        
        cmds = command.split()

        match cmds[0]:
            case "help":
                log.write("help")
            case "exit":
                log.write("exit")
            case "clear":
                log.clear()
            case "reset":
                log.write("reset")
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
    

    # def is_valid_command(self, value: str) -> bool:
    #     try:
    #         return value.split()[0] in self.valid_base_commands
    #     except ValueError:
    #         return False

    
    # @on(Input.Submitted)
    # def show_invalid_reasons(self, event: Input.Submitted) -> None:
    #     # Updating the UI to show the reasons why validation failed
    #     if not event.validation_result.is_valid:  
    #         for reason in event.validation_result.failure_descriptions:
    #             self.query_one(RichLog).write(f"[red]{reason}")


if __name__ == "__main__":
    app = spellb00k()
    app.run()
    
    