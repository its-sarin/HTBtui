from dataclasses import dataclass
from textual.message import Message
from enums.debug_level import DebugLevel

@dataclass
class DebugMessage(Message):
    debug_data: dict
    debug_level: DebugLevel