from dataclasses import dataclass
from textual.message import Message

@dataclass
class DataReceived(Message):
    data: dict
    key: str