import os

from textual.app import App, ComposeResult
from textual.widgets import RichLog, Static, Input, Footer, Header
from textual.containers import Container

from htb import HTBClient

# get api key from environment variable
API_KEY = os.environ['HTB_API_KEY']

htb = HTBClient(API_KEY)    

class spellb00k(App):
    CSS_PATH = "htb.tcss"

    def compose(self) -> ComposeResult:
        yield Header()

        yield Container(
            Container(
                Static(id="player"),
                Static(id="season"),
                id="stats_container"
            ),
            Static(
                id="machine_list"
            ),      
            id="sidebar",
            classes="box"
        )
        yield Container(
            RichLog(highlight=True, markup=True, auto_scroll=True, id="console"),
            Input(placeholder="Enter a command", id="input"),
            classes="box",
            id="main"
        )
        yield Container(
            Static(id="vpn_connection"),
            classes="box",
            id="footer_left"
        )
        yield Container(
            Static(id="active_machine"),
            classes="box",
            id="footer_right"
        )

    def on_ready(self) -> None:
        """Called  when the DOM is ready."""
        log = self.query_one(RichLog)
        log.write("[bold purple]Welcome to spellb00k!")
        
    def on_input_submitted(self, message: Input.Submitted) -> None:
        log = self.query_one(RichLog)
        log.write(message.value)
        message.control.clear()

    async def on_mount(self) -> None:
        self.title = "spellb00k [HTB module]"
        self.sub_title = "by sar1n"  
        self.run_worker(self.update_connection())
        self.run_worker(self.update_profile())
        self.run_worker(self.update_season())
        self.run_worker(self.update_machine_list())
        self.run_worker(self.update_active_machine())

        self.check_vpn = self.set_interval(10, self.update_connection)
        self.check_active_machine = self.set_interval(10, self.update_active_machine)
        
    async def update_connection(self) -> None:
        vpn_widget = self.query_one("#vpn_connection", Static)
        log = self.query_one(RichLog)
        data = await htb.get_connection_status()
        log.write(data)
        vpn_widget.update(htb.make_connection())

    async def update_profile(self) -> None:
        player_widget = self.query_one("#player", Static)
        log = self.query_one(RichLog)
        data = await htb.get_profile()
        log.write(data)
        player_widget.update(htb.make_profile())

    async def update_season(self) -> None:
        season_widget = self.query_one("#season", Static)
        log = self.query_one(RichLog)
        data = await htb.get_season_data()
        log.write(data)
        season_widget.update(htb.make_season())

    async def update_machine_list(self) -> None:
        machine_list_widget = self.query_one("#machine_list", Static)
        log = self.query_one(RichLog)
        data = await htb.get_machine_list()
        log.write(data)
        machine_list_widget.update(htb.make_machine_list())

    async def update_active_machine(self) -> None:
        active_machine_widget = self.query_one("#active_machine", Static)
        log = self.query_one(RichLog)
        data = await htb.get_active_machine()
        log.write(data)
        active_machine_widget.update(htb.make_active_machine())


if __name__ == "__main__":
    app = spellb00k()
    app.run()
    
    