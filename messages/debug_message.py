from dataclasses import dataclass
from textual.message import Message
from enums.debug_level import DebugLevel

@dataclass
class DebugMessage(Message):
    data: dict
    debug_level: DebugLevel