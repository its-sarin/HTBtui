from textual import on
from textual.widgets import RichLog

from messages.debug_message import DebugMessage
from messages.data_received import DataReceived
from messages.log_message import LogMessage
from enums.debug_level import DebugLevel


class OutputLog(RichLog):
    """
    A widget for displaying log messages.
    """

    def __init__(self, *args, **kwargs) -> None:
        """
        Initializes the widget.
        """
        super().__init__(*args, **kwargs)

    # def _on_click(self) -> None:
    #     """
    #     Event handler for when the widget is clicked.
    #     """
    #     self.toggle_class("expanded")

    @on(DebugMessage)
    def log_debug_messages(self, message: DebugMessage) -> None:
        """
        Logs debug messages to the console.

        Args:
            message (DebugMessage): The debug message to log.
        """
        if message.debug_level.value <= self.debug_level.value:
            self.write(message.debug_data)

    @on(DataReceived)
    def log_data_received(self, message: DataReceived) -> None:
        """
        Logs data received messages to the console.

        Args:
            message (DataReceived): The data received message to log.
        """
        self.write(message.data)

    @on(LogMessage)
    def log_messages(self, message: LogMessage) -> None:
        """
        Logs log messages to the console.

        Args:
            message (LogMessage): The log message to log.
        """
        self.write(message.message)
