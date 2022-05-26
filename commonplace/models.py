from dataclasses import dataclass, field
from datetime import datetime, time
from enum import Enum
import re
from typing import List


class WorkState(str, Enum):
    NEW = "new"
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    DONE = "done"


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
    state_marks = dict = {
        "x": WorkState.DONE,
        "w": WorkState.WAITING,
        "p": WorkState.IN_PROGRESS,
    }
    state_mark_pattern = re.compile(f"^\\{left_state_bracket}\\s*([{''.join(state_marks.keys())}]?)\\s*\\{right_state_bracket}")
    week_days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    daily_pattern = re.compile("(every day|today)", re.IGNORECASE)
    weekly_pattern = re.compile(f"every ({'|'.join(week_days)})", re.IGNORECASE)
    nths = ["2nd", "3rd", "4th"]
    n_weekly_pattern = re.compile(f"every ({'|'.join(nths)}) ({'|'.join(week_days)})", re.IGNORECASE)
    monthly_pattern = re.compile(r"every (\d{1,2})\.?$", re.IGNORECASE)
    yearly_pattern = re.compile(r"every (\d{1,2})\.(\d{1,2})\.?$", re.IGNORECASE)
    fixed_time: datetime | None = None

    def now(self):
        return self.fixed_time if self.fixed_time else datetime.now()


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
    doc_pos: DocPosition | None = False
    color: str = ""
    priority: int = 0


@dataclass
class Comment:
    content: str
    doc_pos: DocPosition


@dataclass
class MomentDateTime:
    dt: datetime  # pylint: disable=invalid-name
    doc_pos: DocPosition | None = None


@dataclass
class Moment:  # pylint: disable=too-many-instance-attributes
    name: str = ""
    comments: List[Comment] = field(default_factory=list)
    sub_moments: List = field(default_factory=list)
    work_state: WorkState = WorkState.NEW
    priority: int = 0
    category: Category | None = None
    time_of_day: MomentDateTime | None = None
    doc_pos: DocPosition | None = None


@dataclass
class SingleMoment(Moment):
    start: MomentDateTime | None = None
    end: MomentDateTime | None = None


class RecurrenceType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    BI_WEEKLY = "biweekly"
    TRI_WEEKLY = "triweekly"
    QUADRI_WEEKLY = "quadriweekly"


@dataclass
class Recurrence:
    recurrence_type: RecurrenceType
    ref_date: MomentDateTime


@dataclass
class RecurringMoment(Moment):
    recurrence: Recurrence | None = None


@dataclass
class Todos:
    categories: List[Category] = field(default_factory=list)
    moments: List[Moment] = field(default_factory=list)


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
