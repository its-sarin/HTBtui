from textual import on
from textual.app import App
from textual.widgets import RichLog

from screens.htb_screen import HTBScreen
from screens.console_modal import ConsoleModal

from messages.debug_message import DebugMessage
from enums.debug_level import DebugLevel


class spellb00k(App):

    BINDINGS = [("`", "request_console", "Show Console")]
        
    SCREENS = {
        "htb_screen": HTBScreen(),
        "console_modal": ConsoleModal()
    }

    debug_level = DebugLevel.NONE
    
    def on_ready(self) -> None:
        """
        Event handler for when the application is ready.
        """

    async def on_mount(self) -> None:
        """
        Event handler for when the application is mounted.
        """
        self.push_screen("htb_screen")

    def action_request_console(self) -> None:
        """
        Opens the console modal.
        """
        # log = self.query_one(RichLog)
        # log.write("Console requested")
        self.push_screen("console_modal")
        
    @on(DebugMessage)
    def log_debug_messages(self, message: DebugMessage) -> None:
        """
        Logs debug messages to the console.

        Args:
            message (DebugMessage): The debug message to log.
        """
        if message.debug_level.value <= self.debug_level.value:
            try:
                log = self.query_one(RichLog)
                log.write(message.data)
            except Exception as e:
                print(f"Error: {e}")


if __name__ == "__main__":
    app = spellb00k()
    app.run()
    
    