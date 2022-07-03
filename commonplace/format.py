from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List

from commonplace.instantiate import generate_instances_of_moment
from commonplace.models import (DocPosition, Moment, Outline, RecurringMoment, SingleMoment, Todos, WorkState)
from commonplace.util import get_bottom_line, with_start_of_day

TODO_FORMAT = "todo"
TRASH_FORMAT = "trash"
CAT_STYLE = "cat"
MOM_STYLE = "mom"
COM_STYLE = "com"
DATE_STYLE = "date"
TIME_STYLE = "time"
DONE_SUFFIX = ".done"
PRIORITY_SUFFIX = ".priority"
UNTIL_SUFFIX = ".until"


@dataclass
class FormatState:
    raw_content: str
    format: str = ""
    last_style: str = ""
    last_style_start: int = 0
    last_style_end: int = 0
    fixed_time: datetime | None = None


def format_todos(todos: Todos, raw_content: str, format_type: str = TODO_FORMAT, fixed_time=None) -> str:
    state = FormatState(raw_content=raw_content, fixed_time=fixed_time)

    for cat in todos.categories:
        add_format_line(state, CAT_STYLE, cat.doc_pos)

    for mom in todos.moments:
        if format_type == TODO_FORMAT:
            format_moment(state, mom)
        elif format_type == TRASH_FORMAT:
            format_trash_moment(state, mom)
        else:
            raise ValueError(f"Unknown format '{format_type}'")

    if state.last_style:
        flush_last_style(state)

    return state.format


def format_moment(state: FormatState, mom: Moment, parent_done=False):
    style = MOM_STYLE
    done = parent_done or mom.work_state == WorkState.DONE
    if done:
        style += DONE_SUFFIX
    else:
        style += format_due_soon(mom, fixed_time=state.fixed_time)
        if mom.priority > 0:
            style += PRIORITY_SUFFIX

    add_format_line(state, style, mom.doc_pos)

    if done:
        for com in mom.comments:
            add_format_line(state, COM_STYLE + DONE_SUFFIX, com.doc_pos)
    else:
        format_dates(state, mom)

    for sub in mom.sub_moments:
        format_moment(state, sub, parent_done=done)


def format_trash_moment(state: FormatState, mom: Moment):
    add_format_line(state, MOM_STYLE, mom.doc_pos)
    format_dates(state, mom)

    for sub in mom.sub_moments:
        format_trash_moment(state, sub)


def format_dates(state: FormatState, mom: Moment):
    if isinstance(mom, SingleMoment):
        if mom.start:
            add_format_line(state, DATE_STYLE, mom.start.doc_pos)
        if mom.end and (not mom.start or mom.end.doc_pos != mom.start.doc_pos):
            add_format_line(state, DATE_STYLE, mom.end.doc_pos)

    elif isinstance(mom, RecurringMoment):
        add_format_line(state, DATE_STYLE, mom.recurrence.ref_date.doc_pos)

    if mom.time_of_day:
        add_format_line(state, TIME_STYLE, mom.time_of_day.doc_pos)


def format_due_soon(mom: Moment, fixed_time=None):
    # Due until 10 (n-1) days in the future
    cutoff = 11
    today = with_start_of_day(fixed_time if fixed_time else datetime.now()).astimezone(tz=None)
    n_days_from_today = today + timedelta(days=cutoff)
    n_real_hours = (n_days_from_today - today) / timedelta(hours=1)
    instances = generate_instances_of_moment(mom, today, n_days_from_today, incl_subs=False)
    earliest = cutoff
    for inst in instances:
        due = inst.end - today
        # We need to compare hours here because of daylight saving time.
        # Instead of 264h (=11 days) it might only be 263h or 265h,
        # which would lead to the wrong number of days calculated.
        if due / timedelta(hours=1) >= n_real_hours:
            continue

        due_days = int(due / timedelta(days=1))
        if due_days < earliest:
            earliest = due_days

    if earliest < cutoff:
        return UNTIL_SUFFIX + str(earliest)

    return ""


def add_format_line(state: FormatState, style: str, pos: DocPosition):
    if state.last_style and style == state.last_style and only_whitespace_between(state.last_style_end, pos.offset,
                                                                                  state.raw_content):
        state.last_style_end = pos.offset + pos.length
    else:
        if state.last_style:
            flush_last_style(state)
        state.last_style = style
        state.last_style_start = pos.offset
        state.last_style_end = pos.offset + pos.length


def flush_last_style(state: FormatState):
    state.format += f"{state.last_style_start},{state.last_style_end},{state.last_style}\n"


def only_whitespace_between(start, end, raw_content):
    return all((c.isspace() for c in raw_content[start:end]))


def fold_todos(todos: Todos) -> str:
    folds = ""
    for mom in todos.moments:
        start = mom.doc_pos.line_num
        end = get_bottom_line(mom)
        if end > start:
            folds += f"{start}-{end}\n"

    return folds


def outline_todos(todos: Todos, raw_content: str, format_type: str = TODO_FORMAT) -> List[Outline]:
    return [outline(mom, raw_content) for mom in todos.moments if format_type != TODO_FORMAT or mom.work_state != WorkState.DONE]


def outline(mom: Moment, raw_content: str) -> Outline:
    detail = ""
    if isinstance(mom, SingleMoment):
        if mom.start:
            detail += extract(raw_content, mom.start.doc_pos)
        if mom.end and (not mom.start or mom.end.doc_pos != mom.start.doc_pos):
            detail += " - " + extract(raw_content, mom.end.doc_pos)

    elif isinstance(mom, RecurringMoment):
        detail += extract(raw_content, mom.recurrence.ref_date.doc_pos)

    if mom.time_of_day:
        detail += " " + extract(raw_content, mom.time_of_day.doc_pos)

    return Outline(
        name=mom.name,
        start_line=mom.doc_pos.line_num,
        end_line=get_bottom_line(mom),
        detail=detail,
    )


def extract(content: str, doc_pos: DocPosition) -> str:
    return content[doc_pos.offset:doc_pos.offset + doc_pos.length]
