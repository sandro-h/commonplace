import re
from typing import Iterable

from commonplace.models import Line

NEWLINE_PATTERN = re.compile(r"(\n)")


class LineIterator:

    def __init__(self, lines: Iterable[str]):
        self._lines = lines
        self._line_number = 0
        self._offset = 0
        self._last_line = None
        self._undoing = False
        self._checked_nl = False
        self._extra_nl_len = 0

    def undo(self):
        self._undoing = True

    def __next__(self):
        if self._undoing:
            line = self._last_line
            self._line_number -= 1
            self._offset -= len(line) + self._extra_nl_len
            self._undoing = False
        else:
            line = next(self._lines, None)
            # Explicitly return last line if empty, since we'd lose this information because
            # we strip newlines in the returned content
            if line is None and self._last_line is not None and self._last_line.endswith("\n"):
                line = ""

        if line is None:
            raise StopIteration

        if not self._checked_nl:
            self._checked_nl = True
            if hasattr(self._lines, "newlines"):
                # Python silently ignores carrier return and only adds \n to the line
                if self._lines.newlines == "\r\n":
                    self._extra_nl_len = 1

        result = Line(
            content=line.rstrip(),
            line_num=self._line_number,
            offset=self._offset,
        )

        self._last_line = line
        self._line_number += 1
        self._offset += len(line) + self._extra_nl_len

        return result


def StringLineIterator(content: str) -> LineIterator:  # pylint: disable=invalid-name
    return LineIterator(split_like_file(content))


def split_like_file(content):
    prev = None
    for line in NEWLINE_PATTERN.split(content):
        if prev is None:
            prev = line
        else:
            yield prev + "\n"
            prev = None

    if prev:  # deliberately also ignoring empty string
        yield prev
