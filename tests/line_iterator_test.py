from commonplace.line_iterator import StringLineIterator
from commonplace.models import Line


def test_read_lines():
    lines = """\
line1
line2
line3
line4\
"""

    line_iter = StringLineIterator(lines)

    assert next(line_iter) == Line("line1", 1, 0)
    assert next(line_iter) == Line("line2", 2, 6)
    assert next(line_iter) == Line("line3", 3, 12)
    assert next(line_iter) == Line("line4", 4, 18)
    assert next(line_iter, None) is None


def test_read_empty_last_line():
    lines = """\
line1
line2
line3
line4
"""

    line_iter = StringLineIterator(lines)

    assert next(line_iter) == Line("line1", 1, 0)
    assert next(line_iter) == Line("line2", 2, 6)
    assert next(line_iter) == Line("line3", 3, 12)
    assert next(line_iter) == Line("line4", 4, 18)
    assert next(line_iter) == Line("", 5, 24)
    assert next(line_iter, None) is None


def test_carrier_return():
    lines = "line1\r\nline2\r\nline3\r\nline4"

    line_iter = StringLineIterator(lines)

    assert next(line_iter) == Line("line1", 1, 0)
    assert next(line_iter) == Line("line2", 2, 7)
    assert next(line_iter) == Line("line3", 3, 14)
    assert next(line_iter) == Line("line4", 4, 21)
    assert next(line_iter, None) is None


def test_undo():
    lines = """\
line1
line2
line3
line4\
"""

    line_iter = StringLineIterator(lines)

    assert next(line_iter) == Line("line1", 1, 0)
    assert next(line_iter) == Line("line2", 2, 6)
    line_iter.undo()
    assert next(line_iter) == Line("line2", 2, 6)
    assert next(line_iter) == Line("line3", 3, 12)
    line_iter.undo()
    assert next(line_iter) == Line("line3", 3, 12)
    assert next(line_iter) == Line("line4", 4, 18)
    assert next(line_iter, None) is None


def test_repeated_undo():
    lines = """\
line1
line2
line3
line4\
"""

    line_iter = StringLineIterator(lines)

    assert next(line_iter) == Line("line1", 1, 0)
    assert next(line_iter) == Line("line2", 2, 6)
    assert next(line_iter) == Line("line3", 3, 12)
    line_iter.undo()
    assert next(line_iter) == Line("line3", 3, 12)
    line_iter.undo()
    assert next(line_iter) == Line("line3", 3, 12)
    line_iter.undo()
    assert next(line_iter) == Line("line3", 3, 12)
    assert next(line_iter) == Line("line4", 4, 18)
    assert next(line_iter, None) is None


def test_undo_last():
    lines = """\
line1
line2
line3
line4\
"""

    line_iter = StringLineIterator(lines)

    assert next(line_iter) == Line("line1", 1, 0)
    assert next(line_iter) == Line("line2", 2, 6)
    assert next(line_iter) == Line("line3", 3, 12)
    assert next(line_iter) == Line("line4", 4, 18)
    line_iter.undo()
    assert next(line_iter) == Line("line4", 4, 18)
    assert next(line_iter, None) is None
