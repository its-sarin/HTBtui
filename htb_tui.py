from textual import on
from textual.app import App

from screens import HTBScreen, ConsoleModal

from messages import DebugMessage, DataReceived, LogMessage
from enums import DebugLevel


class HTBtui(App):

    BINDINGS = [("`", "expand_log", "Show Log"), ("~", "request_console", "Show Console")]
        
    SCREENS = {
        "htb_screen": HTBScreen(),
        "console_modal": ConsoleModal()
    }


    def __init__(self) -> None:
        super().__init__()
        self.message_queue = []
        self.context_data = {}
        self.debug_level = DebugLevel.LOW
    
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
        log = self.query_one("#log")
        log.write("Console requested")
        self.push_screen("console_modal")

    def action_expand_log(self) -> None:
        """
        Opens the console modal.
        """
        # log = self.query_one(RichLog)
        # log.write("Console requested")
        # self.push_screen("console_modal")
        self.query_one("#log").toggle_class("expanded")

    def action_test_clear(self) -> None:
        """
        Clears the log.
        """
        test = self.query_one("#machine_control")
        test.active_machine_data = {}
    
    @on(DataReceived)
    def add_data_to_context(self, message: DataReceived) -> None:
        """
        Adds data to the context.

        Args:
            message (DataReceived): The data to add to the context.
        """
        self.context_data[message.key] = message.data
        # self.query_one(RichLog).write(f"Data received: {message.key}")
        # self.query_one(RichLog).write(self.context_data[message.key])

    @on(DebugMessage)
    def log_debug_messages(self, message: DebugMessage) -> None:
        """
        Logs debug messages to the console.

        Args:
            message (DebugMessage): The debug message to log.
        """
        if message.debug_level.value <= self.debug_level.value:
            log = self.query_one("#log")
            log.write(message.debug_data)

    @on(LogMessage)
    def log_messages(self, message: LogMessage) -> None:
        """
        Logs messages to the console.

        Args:
            message (LogMessage): The message to log.
        """
        log = self.query_one("#log")
        log.write(message.message)


if __name__ == "__main__":
    app = HTBtui()
    app.run()
    
    