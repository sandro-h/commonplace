from dataclasses import dataclass, field
from datetime import datetime, time
from enum import Enum
from typing import List


class WorkState(str, Enum):
    NEW = "new"
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    DONE = "done"


@dataclass
class DocPosition:
    line_num: int
    offset: int
    length: int


@dataclass
class Category:
    name: str
    doc_pos: DocPosition | None = False
    color: str = ""
    priority: int = 0


@dataclass
class Instance:  # pylint: disable=too-many-instance-attributes
    name: str
    start: datetime
    end: datetime
    ends_in_range: bool
    origin_doc_pos: DocPosition | None = None
    time_of_day: time | None = None
    priority: int = 0
    category: Category | None = None
    done: bool = False
    work_state: WorkState = WorkState.NEW
    sub_instances: List = field(default_factory=list)
