import httpx
import pyperclip

from rich.table import Table
from rich import box

from textual.widgets import Static

from messages.debug_message import DebugMessage
from enums.debug_level import DebugLevel
from utilities.api_token import APIToken

class VPNConnection(Static):
    """Static widget that shows the current VPN connection status."""

    token_name = "HTB_TOKEN"
    base_url = "https://labs.hackthebox.com"
    endpoint = "/api/v4/connection/status"
    headers = {
            "Authorization": f"Bearer {APIToken(token_name).get_token()}",
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "HTBClient/1.0.0"
        }

    def __init__(self) -> None:
        super().__init__()                
        self.loading = True
        self.refresh_interval = 10
        self.connection_data = {
            "status": None,
            "location_type_friendly": None,
            "server": {
                "id": None,
                "hostname": None,
                "port": None,
                "friendly_name": None
            },
            "connection": {
                "through_pwnbox": None,
                "ip4": None,
                "ip6": None,
                "down": None,
                "up": None
            }
        }

    async def on_mount(self) -> None:
        """Mount the widget."""
        self.loading = True

        self.run_worker(self.update_connection())
        self.refresh_connection = self.set_interval(self.refresh_interval, self.update_connection)   

    def _on_click(self) -> None:
        """
        Event handler for when the widget is clicked.
        """
        try:
            pyperclip.copy(self.connection_data["connection"]["ip4"])
            self.notify("IP copied to clipboard")
            self.post_message(DebugMessage({"Copied IP": self.connection_data["connection"]["ip4"]}, DebugLevel.LOW))
        except Exception as e:
            self.post_message(DebugMessage({"Error": e}, DebugLevel.LOW))

    async def update_connection(self) -> None:
        """
        Updates the machine list widget with the latest machine list data from HTB.
        """       
        try:
            table: Table = await self.get_connection_status()
            self.loading = False
            self.update(table)
        except Exception as e:
            self.update(f"Error: {e}")

    async def get_connection_status(self):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url + self.endpoint, headers=self.headers)
                if response.status_code == 200:
                    data = response.json()

                    self.post_message(DebugMessage({"VPN Connection Data": data}, DebugLevel.HIGH))

                    # assign data to self.connection_data
                    if data != []:
                        self.connection_data["status"] = "Active"
                        self.connection_data["location_type_friendly"] = data[0]["location_type_friendly"]
                        self.connection_data["server"]["id"] = data[0]["server"]["id"]
                        self.connection_data["server"]["hostname"] = data[0]["server"]["hostname"]
                        self.connection_data["server"]["port"] = data[0]["server"]["port"]
                        self.connection_data["server"]["friendly_name"] = data[0]["server"]["friendly_name"]
                        self.connection_data["connection"]["through_pwnbox"] = data[0]["connection"]["through_pwnbox"]
                        self.connection_data["connection"]["ip4"] = data[0]["connection"]["ip4"]
                        self.connection_data["connection"]["ip6"] = data[0]["connection"]["ip6"]
                        self.connection_data["connection"]["down"] = data[0]["connection"]["down"]
                        self.connection_data["connection"]["up"] = data[0]["connection"]["up"]

                        return self.make_connection()

                    else:
                        self.connection_data["status"] = "No active connection"

                        return self.connection_data["status"]

                else:
                    self.connection_data["status"] = f"No response: {response.status_code}"

                    return self.connection_data["status"]
        except Exception as e:
            return f"Error: {e}"

    def make_connection(self):
        if self.connection_data["status"] != "Active":
            return f"[red bold]{self.connection_data["status"]}"

        # table = Table(
        #     box=box.SIMPLE,
        #     show_header=False,
        #     show_footer=False,
        #     pad_edge=False,
        #     expand=True
        # )

        # table.add_column()

        # table.add_row(self.connection_data["location_type_friendly"] + " -- " + f"[#9fef00]{self.connection_data["connection"]["ip4"]}")
        # table.add_row(self.connection_data["server"]["hostname"], )
        # table.add_row("Pwnbox Active" if self.connection_data["connection"]["through_pwnbox"] else "Pwnbox Inactive")
        # table.add_row(f"↑ {self.connection_data["connection"]["down"]} : ↓ {self.connection_data["connection"]["up"]}")

        return f"{self.connection_data["location_type_friendly"]} :: [#9fef00]{self.connection_data["connection"]["ip4"]}"