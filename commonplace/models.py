from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List


@dataclass
class ParseConfig:  # pylint: disable=too-many-instance-attributes

    category_delim: str = "------"
    priority_mark: str = "!"
    tab_size: int = 4
    left_state_bracket: str = "["
    right_state_bracket: str = "]"
    left_date_bracket: str = "("
    right_date_bracket: str = ")"
    date_formats: List[str] = field(default_factory=lambda: ["%d.%m.%y", "%d.%m.%Y"])
    time_format: str = "%H:%M"
    done_mark: str = "x"
    waiting_mark: str = "w"
    in_progress_mark: str = "p"


@dataclass
class Line:
    content: str
    line_num: int
    offset: int


@dataclass
class DocPosition:
    line_num: int
    offset: int
    length: int


@dataclass
class Category:
    name: str
    doc_pos: DocPosition
    color: str = ""
    priority: int = 0


@dataclass
class Comment:
    content: str
    doc_pos: DocPosition


class WorkState(str, Enum):
    NEW = "new"
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    DONE = "done"


@dataclass
class MomentDateTime:
    dt: datetime  # pylint: disable=invalid-name
    doc_pos: DocPosition


@dataclass
class Moment:
    name: str = ""
    comments: List[Comment] = field(default_factory=list)
    sub_moments: List = field(default_factory=list)
    work_state: WorkState = WorkState.NEW
    priority: int = 0
    category: Category = None
    doc_pos: DocPosition = None


@dataclass
class SingleMoment(Moment):
    start: MomentDateTime = None
    end: MomentDateTime = None
    time_of_day: MomentDateTime = None


@dataclass
class RecurringMoment(Moment):
    pass


@dataclass
class Todos:
    categories: List[Category] = field(default_factory=list)
    moments: List[Moment] = field(default_factory=list)
