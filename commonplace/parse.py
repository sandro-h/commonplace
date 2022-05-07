from dataclasses import dataclass
from typing import Iterable, Tuple

from commonplace.line_iterator import LineIterator, StringLineIterator
from commonplace.models import Category, DocPosition, Line, ParseConfig, Todos


@dataclass
class ParseState:
    config: ParseConfig
    line_iter: LineIterator
    todos: Todos


def parse_moments_file(path: str, config: ParseConfig) -> Todos:
    with open(path, "r", encoding="utf8") as file:
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
    else:
        pass


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


def _each_line(line_iter: LineIterator):
    while True:
        line = next(line_iter, None)
        if line is None:
            break
        yield line


def _is_blank(content: str):
    return not content.strip()
