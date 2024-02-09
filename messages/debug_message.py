from dataclasses import dataclass
from textual.message import Message
from enums import DebugLevel

@dataclass
class DebugMessage(Message):
    debug_data: dict
    debug_level: DebugLevel