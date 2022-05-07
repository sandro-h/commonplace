from dataclasses import dataclass
from typing import Iterable, List

from commonplace.line_iterator import LineIterator, StringLineIterator
from commonplace.models import ParseConfig


@dataclass
class ParseState:
    config: ParseConfig
    line_iter: LineIterator


def parse_moments_file(path: str, config: ParseConfig) -> List:
    with open(path, "r", encoding="utf8") as file:
        return _parse_moments(LineIterator(file), config)


def parse_moments_string(content: str, config: ParseConfig) -> List:
    return _parse_moments(StringLineIterator(content), config)


def parse_moments(lines: Iterable[str], config: ParseConfig) -> List:
    return _parse_moments(LineIterator(lines), config)


def _parse_moments(line_iter: LineIterator, config: ParseConfig) -> List:
    state = ParseState(config=config, line_iter=line_iter)
    for line in next_line(state.line_iter):
        print(line)


def next_line(line_iter: LineIterator):
    while True:
        line = next(line_iter, None)
        if line is None:
            break
        yield line
