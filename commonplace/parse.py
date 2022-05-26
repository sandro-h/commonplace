import dataclasses
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable, Tuple

from commonplace.line_iterator import LineIterator, StringLineIterator
from commonplace.models import (Category, Comment, DocPosition, Line, Moment, MomentDateTime, ParseConfig, Recurrence,
                                RecurrenceType, RecurringMoment, SingleMoment, Todos, WorkState)
from commonplace.util import epoch_week, with_end_of_day, with_weekday


@dataclass
class ParseState:
    config: ParseConfig
    line_iter: LineIterator
    todos: Todos


def parse_moments_file(path: str, config: ParseConfig) -> Todos:
    with open(path, "rU", encoding="utf8") as file:
        return _parse_moments(LineIterator(file), config)


def parse_moments_string(content: str, config: ParseConfig) -> Todos:
    return _parse_moments(StringLineIterator(content), config)


def parse_moments(lines: Iterable[str], config: ParseConfig) -> Todos:
    return _parse_moments(LineIterator(lines), config)


def _parse_moments(line_iter: LineIterator, config: ParseConfig) -> Todos:
    state = ParseState(config=config, line_iter=line_iter, todos=Todos())
    for line in _each_line(state.line_iter):
        _parse_line(line, state)

    return state.todos


def _parse_line(line: Line, state: ParseState):
    if _is_blank(line.content):
        return

    if _is_category_delimiter(line, state.config):
        _parse_category_block(state)
    elif line.content.startswith(state.config.left_state_bracket):
        _parse_top_moment_block(line, state)


def _parse_category_block(state: ParseState):
    cat_line = next(state.line_iter, None)
    if cat_line is None:
        # Expected a category name after category delimiter
        return

    line_after_cat = next(state.line_iter, None)
    if not _is_category_delimiter(line_after_cat, state.config):
        # Expected closing delimiter line
        return

    state.todos.categories.append(_parse_category(cat_line, state.config))


def _parse_category(line: Line, config: ParseConfig) -> Category:
    content = line.content
    color, content = _parse_category_color(content)
    priority, content = _parse_priority(content, config)
    return Category(
        name=content.lstrip(),
        color=color,
        priority=priority,
        doc_pos=DocPosition(
            line_num=line.line_num,
            offset=line.offset,
            length=len(line.content),
        ),
    )


def _parse_category_color(content: str) -> Tuple[str, str]:
    start = content.find("[")

    if start < 0 or not content.endswith("]"):
        return "", content

    return content[start + 1:-1], content[:start].strip()


def _parse_priority(content: str, config: ParseConfig) -> Tuple[int, str]:
    prio = 0
    for prio, char in enumerate(reversed(content)):
        if char != config.priority_mark:
            break

    return prio, content[:len(content) - prio].strip()


def _is_category_delimiter(line: Line, config: ParseConfig):
    return line is not None and line.content.startswith(config.category_delim)


def _parse_top_moment_block(line: Line, state: ParseState):
    mom = _parse_moment_block(line, line.content.strip(), state)
    if not mom:
        return

    state.todos.moments.append(mom)


def _parse_moment_block(line: Line, line_content: str, state: ParseState, indent=0):
    mom = _parse_moment_line(line, line_content, state.config)
    if not mom:
        return None

    mom.category = state.todos.categories[-1] if state.todos.categories else None
    _parse_comments_and_sub_moments(mom, state, indent)
    return mom


def _parse_moment_line(line: Line, line_content: str, config: ParseConfig) -> Moment | None:
    mom, line_content = _parse_recurring_moment(line, line_content, config)
    if not mom:
        mom, line_content = _parse_single_moment(line, line_content, config)

    state, line_content = _parse_state_mark(line_content, config)
    if state is None:
        return None
    mom.work_state = state

    mom.priority, line_content = _parse_priority(line_content, config)

    mom.name = line_content

    return mom


def _parse_recurring_moment(line: Line, line_content: str, config: ParseConfig) -> Tuple[RecurringMoment, str]:
    if not line_content.endswith(config.right_date_bracket):
        return None, line_content

    recur, time_of_day, new_line_content = _parse_recurrence(line, line_content, config)
    if not recur:
        return None, line_content

    mom = RecurringMoment(recurrence=recur,
                          time_of_day=time_of_day,
                          doc_pos=DocPosition(
                              line_num=line.line_num,
                              offset=line.offset,
                              length=len(line.content),
                          ))
    return mom, new_line_content


def _parse_recurrence(line: Line, line_content: str, config: ParseConfig) -> Tuple[Recurrence, MomentDateTime, str]:
    lbracket_pos = line_content.rfind(config.left_date_bracket)
    if lbracket_pos < 0:
        return None, None, line_content

    untrimmed_pos = line.content.rfind(config.left_date_bracket) + 1
    recur_str = line_content[lbracket_pos + 1:-1]
    time_of_day, recur_str = _parse_time_suffix(recur_str, config)
    if time_of_day:
        time_of_day.doc_pos.offset += line.offset + untrimmed_pos

    recur = None
    for parse in [try_parse_daily, try_parse_weekly, try_parse_n_weekly, try_parse_monthly, try_parse_yearly]:
        recur = parse(recur_str, config)
        if recur:
            break

    if not recur:
        return None, None, line_content

    recur.ref_date.doc_pos = DocPosition(
        line_num=line.line_num,
        offset=line.offset + untrimmed_pos,
        length=len(recur_str),
    )

    return recur, time_of_day, line_content[:lbracket_pos].strip()


def try_parse_daily(content: str, config: ParseConfig) -> Recurrence | None:
    if not config.daily_pattern.search(content):
        return None

    return Recurrence(
        recurrence_type=RecurrenceType.DAILY,
        ref_date=MomentDateTime(dt=config.now()),
    )


def try_parse_weekly(content: str, config: ParseConfig) -> Recurrence | None:
    match = config.weekly_pattern.search(content)
    if not match:
        return None

    weekday = _parse_weekday(match.group(1), config)
    if weekday < 0:
        return None

    ref_date = with_weekday(config.now(), weekday)
    return Recurrence(
        recurrence_type=RecurrenceType.WEEKLY,
        ref_date=MomentDateTime(dt=_with_start_of_day(ref_date.astimezone(tz=None))),
    )


def _parse_weekday(content: str, config: ParseConfig) -> int:
    return config.week_days.index(content.lower())


def _with_start_of_day(date: datetime) -> datetime:
    return date.replace(hour=0, minute=0, second=0, microsecond=0)


def try_parse_n_weekly(content: str, config: ParseConfig) -> Recurrence | None:
    match = config.n_weekly_pattern.search(content)
    if not match:
        return None

    nth, nth_recur_type = _parse_nth(match.group(1), config)
    if not nth_recur_type:
        return None

    weekday = _parse_weekday(match.group(2), config)
    if weekday < 0:
        return None

    ref_date = with_weekday(config.now(), weekday)
    week_offset = epoch_week(ref_date) % nth
    ref_date += timedelta(days=-7 * week_offset)
    return Recurrence(
        recurrence_type=nth_recur_type,
        ref_date=MomentDateTime(dt=_with_start_of_day(ref_date.astimezone(tz=None))),
    )


def _parse_nth(content: str, config: ParseConfig) -> Tuple[int, RecurrenceType]:
    nth = config.nths.index(content.lower())
    if nth == 0:
        return 2, RecurrenceType.BI_WEEKLY
    if nth == 1:
        return 3, RecurrenceType.TRI_WEEKLY
    if nth == 2:
        return 4, RecurrenceType.QUADRI_WEEKLY

    return None, None


def try_parse_monthly(content: str, config: ParseConfig) -> Recurrence | None:
    match = config.monthly_pattern.search(content)
    if not match:
        return None

    try:
        day = int(match.group(1))
    except ValueError:
        return None

    now = config.now()
    ref_date = datetime(year=now.year, month=now.month, day=day, hour=0, minute=0, second=0, microsecond=0)
    return Recurrence(
        recurrence_type=RecurrenceType.MONTHLY,
        ref_date=MomentDateTime(dt=ref_date.astimezone(tz=None)),
    )


def try_parse_yearly(content: str, config: ParseConfig) -> Recurrence | None:
    match = config.yearly_pattern.search(content)
    if not match:
        return None

    try:
        day = int(match.group(1))
        month = int(match.group(2))
    except ValueError:
        return None

    now = config.now()
    ref_date = datetime(year=now.year, month=month, day=day, hour=0, minute=0, second=0, microsecond=0)
    return Recurrence(
        recurrence_type=RecurrenceType.YEARLY,
        ref_date=MomentDateTime(dt=ref_date.astimezone(tz=None)),
    )


def _parse_single_moment(line: Line, line_content: str, config: ParseConfig) -> Tuple[SingleMoment, str]:
    start = None
    end = None
    time_of_day = None
    if line_content.endswith(config.right_date_bracket):
        start, end, time_of_day, line_content = _parse_date_suffix(line, line_content, config)

    return SingleMoment(start=start,
                        end=end,
                        time_of_day=time_of_day,
                        doc_pos=DocPosition(
                            line_num=line.line_num,
                            offset=line.offset,
                            length=len(line.content),
                        )), line_content


def _parse_date_suffix(line: Line, line_content: str,
                       config: ParseConfig) -> Tuple[MomentDateTime, MomentDateTime, MomentDateTime, str]:
    left_pos = line_content.rfind(config.left_date_bracket)
    if left_pos < 0:
        return None, None, None, line_content

    untrimmed_pos = line.content.rfind(config.left_date_bracket) + 1
    suffix_str = line_content[left_pos + 1:-1]
    time_of_day, suffix_str = _parse_time_suffix(suffix_str, config)
    _finalize_doc_pos(time_of_day, line, untrimmed_pos)

    suffix_str = suffix_str.strip()
    start = None
    end = None
    # Try all dashes as separator in case the date format uses dashes (e.g. 2015-12-24 - 2016-02-03)
    dash_offset = 0
    dash_pos = suffix_str.find("-")
    while dash_pos >= 0 and start is None:
        start, end = _parse_date_range(suffix_str, dash_offset + dash_pos, config)
        if start is None:
            dash_offset += dash_pos + 1
            dash_pos = suffix_str.find("-", dash_offset)

    if not start:
        start = _parse_date_single(suffix_str, config)
        if start:
            end = dataclasses.replace(start)
            end.doc_pos = dataclasses.replace(start.doc_pos)

    if end:
        end.dt = with_end_of_day(end.dt)

    if start or end:
        _finalize_doc_pos(start, line, untrimmed_pos)
        _finalize_doc_pos(end, line, untrimmed_pos)
        return start, end, time_of_day, line_content[:left_pos].strip()

    return None, None, None, line_content


def _parse_date_range(line_content: str, dash_pos: int, config: ParseConfig) -> Tuple[MomentDateTime, MomentDateTime]:
    start: MomentDateTime | None = None
    end: MomentDateTime | None = None
    start_str = line_content[:dash_pos]
    end_str = line_content[dash_pos + 1:]

    if start_str:
        date = _parse_date(start_str, config)
        if not date:
            return None, None
        start = MomentDateTime(dt=date,
                               doc_pos=DocPosition(
                                   line_num=-1,
                                   offset=_count_start_whitespaces(start_str),
                                   length=_stripped_length(start_str),
                               ))

    if end_str:
        date = _parse_date(end_str, config)
        if not date:
            return None, None
        end = MomentDateTime(dt=date,
                             doc_pos=DocPosition(
                                 line_num=-1,
                                 offset=len(start_str) + 1 + _count_start_whitespaces(end_str),
                                 length=_stripped_length(end_str),
                             ))

    return start, end


def _parse_date_single(line_content: str, config: ParseConfig) -> MomentDateTime | None:
    date = _parse_date(line_content, config)

    if not date:
        return None

    return MomentDateTime(dt=date,
                          doc_pos=DocPosition(
                              line_num=-1,
                              offset=_count_start_whitespaces(line_content),
                              length=_stripped_length(line_content),
                          ))


def _parse_time_suffix(line_content: str, config: ParseConfig) -> Tuple[MomentDateTime, str]:
    trimmed = line_content.strip()
    space_pos = trimmed.rfind(" ")
    if space_pos < 0 or space_pos == len(trimmed) - 1:
        return None, line_content

    time_str = trimmed[space_pos + 1:]
    time_of_day = _parse_time(time_str, config)
    if not time_of_day:
        return None, line_content

    mom_time = MomentDateTime(dt=time_of_day, doc_pos=DocPosition(
        line_num=-1,
        offset=space_pos + 1,
        length=len(time_str),
    ))

    return mom_time, line_content[:space_pos]


def _finalize_doc_pos(date: MomentDateTime, line: Line, offset_delta):
    if date:
        date.doc_pos.line_num = line.line_num
        date.doc_pos.offset += line.offset + offset_delta


def _parse_state_mark(line_content: str, config: ParseConfig) -> Tuple[WorkState, str]:  # pylint: disable=too-many-return-statements
    match_res = config.state_mark_pattern.match(line_content)
    if not match_res:
        return None, line_content

    leftover = line_content[match_res.end() + 1:].strip()
    return config.state_marks.get(match_res.group(1), WorkState.NEW), leftover


def _parse_comments_and_sub_moments(mom: Moment, state: ParseState, indent: int):
    next_indent = indent + state.config.tab_size
    for line in _each_line(state.line_iter):
        line_indent, indent_char_cnt = _count_indent(line.content, state.config.tab_size, next_indent)

        if line_indent >= next_indent:
            _parse_sub_line(mom, line, line.content[indent_char_cnt:], next_indent, state)
        elif _is_blank(line.content):
            if len(mom.comments) > 0:
                # special case: treat empty line between comments as a comment
                mom.comments.append(
                    Comment(
                        content="",
                        doc_pos=DocPosition(line_num=line.line_num, offset=line.offset, length=0),
                    ))
                # Otherwise just ignore the empty line
        else:
            # "Unconsume" the line since it is probably meant for a parent moment up the recursion stack
            state.line_iter.undo()
            break

    # Remove trailing empty comments
    while len(mom.comments) > 0 and mom.comments[-1].content == "":
        mom.comments = mom.comments[:-1]


def _parse_sub_line(mom: Moment, line: Line, line_content: str, indent: int, state: ParseState):
    if line_content.startswith(state.config.left_state_bracket):
        sub_mom = _parse_moment_block(line, line_content, state, indent)
        if sub_mom:
            mom.sub_moments.append(sub_mom)
            return

    # If not a sub moment, assume it's a comment
    _, indent_char_cnt = _count_indent(line.content, state.config.tab_size, indent)
    mom.comments.append(
        Comment(content=line_content,
                doc_pos=DocPosition(
                    line_num=line.line_num,
                    offset=line.offset + indent_char_cnt,
                    length=len(line_content),
                )))


def _parse_date(content, config: ParseConfig) -> datetime | None:
    stripped = content.strip()
    for fmt in config.date_formats:
        try:
            return datetime.strptime(stripped, fmt).astimezone(tz=None)
        except ValueError:
            pass

    return None


def _parse_time(content, config: ParseConfig) -> datetime | None:
    stripped = content.strip()
    try:
        return datetime.strptime(stripped, config.time_format)
    except ValueError:
        pass

    return None


def _count_indent(content, tab_size, max_indent) -> Tuple[int, int]:
    """counts the whitespace indent at the start of the string up to maxIndent.
    Spaces count as 1, Tabs count as tabSize indentation.
    Returns the indentation value and the actual number of whitespace characters."""

    indent = 0
    cnt = 0
    for char in content:
        if char == "\t":
            indent += tab_size
            cnt += 1
        elif char == " ":
            indent += 1
            cnt += 1
        else:
            break

        if indent >= max_indent:
            break

    return indent, cnt


def _each_line(line_iter: LineIterator):
    while True:
        line = next(line_iter, None)
        if line is None:
            break
        yield line


def _is_blank(content: str):
    return not content.strip()


def _count_start_whitespaces(content: str):
    for i, char in enumerate(content):
        if not char.isspace():
            return i
    return len(content)


def _stripped_length(content: str):
    return len(content.strip())
