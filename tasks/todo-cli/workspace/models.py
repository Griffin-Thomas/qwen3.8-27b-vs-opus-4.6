from dataclasses import dataclass
from enum import Enum


class Status(Enum):
    PENDING = "pending"
    DONE = "done"


@dataclass
class Task:
    id: int
    title: str
    status: Status = Status.PENDING
