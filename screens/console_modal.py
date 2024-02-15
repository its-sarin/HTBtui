import httpx

from textual import on
from textual.screen import ModalScreen
from textual.widgets import RichLog, Input
from textual.containers import Container
from textual.suggester import SuggestFromList
from textual.app import ComposeResult

from rich import box
from rich.table import Table

from messages import DebugMessage
from enums import DebugLevel
from utilities import APIToken

class ConsoleModal(ModalScreen):
    """
    Modal screen that displays the console output.
    """

    CSS_PATH = "console_modal.tcss"
    BINDINGS = [("~", "close_console", "Dismiss Console")]

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
        
    def __init__(self) -> None:
        super().__init__()
        self.search_results = None
        self.active_machine_id = None

    def compose(self) -> ComposeResult:
        yield Container(
            RichLog(highlight=True, markup=True, auto_scroll=True, wrap=True, min_width=90, id="console"),
            Input(
                placeholder="Enter a command",
                suggester=SuggestFromList(self.valid_base_commands, case_sensitive=True),
                # validators=[Function(self.is_valid_command, "Invalid command")],
                id="input"
            ),
            id="console_container"
        )

    def action_close_console(self) -> None:
        """
        Closes the console modal.
        """
        self.app.pop_screen()


    def on_input_submitted(self, message: Input.Submitted) -> None:
        """
        Event handler for when an input is submitted.

        Args:
            message (Input.Submitted): The submitted input message.
        """
        # if message.validation_result.is_valid:
        self.run_command(message.value)
        message.control.clear()

    async def fetch_search_results(self, search_type: str, search_term: str) -> None:
        """
        Fetches search results based on the search type and term.

        Args:
            search_type (SearchFilter): The type of search filter.
            search_term (str): The search term.
        """
        log = self.query_one(RichLog)
        log.write(f"[+] Finding {search_type} with name: {search_term} \n") 
        data = await self.get_search_results(search_type, search_term)
        
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
            if search_type == "machine":
                log.write(f"[*] Use the id to start the machine with: start <id>")            
        except Exception as e:
            log.write(f"Error: {str(e)}")
            log.write(f"[!] Error: {e}")

    async def get_search_results(self, filter: str, keyword: str):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url + self.endpoint + '"' + keyword + '"' + '&tags=[\"' + filter + '\"]', headers=self.headers)
                if response.status_code == 200:
                    data = response.json()
                    self.search_results = data

                    return self.search_results
                else:
                    return f"Error: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Error: {e}"

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
        data = await self.spawn_machine(machine_id)
        if "message" in data:
            log.write("[!] " + data["message"])

            if "deployed" in data["message"]:
                self.active_machine_id = machine_id
                log.write("[+] Active machine updated")


    async def stop_machine(self, machine_id: int) -> None:
        """
        Stops the active machine.

        If there is no active machine, it logs a message and returns.
        Otherwise, it retrieves the machine ID of the active machine,
        stops the machine, and logs the result.

        Returns:
            None
        """
        log = self.query_one(RichLog)
        log.write(f"[-] Stopping machine with id: {machine_id}")
        data = await self.terminate_machine(machine_id)
        if "message" in data:
            log.write("[!] " + data["message"])


    async def reset_machine(self, machine_id: int) -> None:
        """
        Resets the active machine.

        This method resets the active machine by calling the `reset_machine` function from the `htb` module.
        If there is no active machine, it logs a message indicating that there is no active machine.

        Returns:
            None
        """
        log = self.query_one(RichLog)
        log.write(f"[+] Resetting machine with id: {machine_id}")
        data = await self.respawn_machine(machine_id)
        log.write("[!] " + data["message"])


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
                if len(cmds) != 2:
                    log.write("Usage: reset <machine_id>")
                else:
                    self.run_worker(self.reset_machine(int(cmds[1])))
            case "start":
                if len(cmds) != 2:
                    log.write("Usage: start <machine_id>")
                else:
                    self.run_worker(self.start_machine(int(cmds[1])))
            case "stop":
                if len(cmds) != 2:
                    log.write("Usage: stop <machine_id>")
                else:
                    self.run_worker(self.stop_machine(int(cmds[1])))
            case "refresh":
                log.write("refresh")
            case "find":
                if len(cmds) < 3 or len(cmds) > 3:
                    log.write("Usage: find <machines|users> <name>")
                else:                     
                    self.run_worker(self.fetch_search_results(cmds[1], cmds[2]))                  
            case _:
                log.write("[red]Invalid command")