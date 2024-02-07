from dataclasses import dataclass
from textual.message import Message

@dataclass
class LogMessage(Message):
    message: str