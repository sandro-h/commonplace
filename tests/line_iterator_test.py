from commonplace.line_iterator import StringLineIterator
from commonplace.models import Line
from tests.test_util import dedent

TEST_LINES = dedent("""\
    line1
    line2
    line3
    line4\
    """)


def test_read_lines():

    line_iter = StringLineIterator(TEST_LINES)

    assert next(line_iter) == Line("line1", 0, 0)
    assert next(line_iter) == Line("line2", 1, 6)
    assert next(line_iter) == Line("line3", 2, 12)
    assert next(line_iter) == Line("line4", 3, 18)
    assert next(line_iter, None) is None


def test_read_empty_last_line():
    lines = dedent("""\
            line1
            line2
            line3
            line4
            """)
    line_iter = StringLineIterator(lines)

    assert next(line_iter) == Line("line1", 0, 0)
    assert next(line_iter) == Line("line2", 1, 6)
    assert next(line_iter) == Line("line3", 2, 12)
    assert next(line_iter) == Line("line4", 3, 18)
    assert next(line_iter) == Line("", 4, 24)
    assert next(line_iter, None) is None


def test_carrier_return():
    lines = "line1\r\nline2\r\nline3\r\nline4"

    line_iter = StringLineIterator(lines)

    assert next(line_iter) == Line("line1", 0, 0)
    assert next(line_iter) == Line("line2", 1, 7)
    assert next(line_iter) == Line("line3", 2, 14)
    assert next(line_iter) == Line("line4", 3, 21)
    assert next(line_iter, None) is None


def test_undo():
    line_iter = StringLineIterator(TEST_LINES)

    assert next(line_iter) == Line("line1", 0, 0)
    assert next(line_iter) == Line("line2", 1, 6)
    line_iter.undo()
    assert next(line_iter) == Line("line2", 1, 6)
    assert next(line_iter) == Line("line3", 2, 12)
    line_iter.undo()
    assert next(line_iter) == Line("line3", 2, 12)
    assert next(line_iter) == Line("line4", 3, 18)
    assert next(line_iter, None) is None


def test_repeated_undo():

    line_iter = StringLineIterator(TEST_LINES)

    assert next(line_iter) == Line("line1", 0, 0)
    assert next(line_iter) == Line("line2", 1, 6)
    assert next(line_iter) == Line("line3", 2, 12)
    line_iter.undo()
    assert next(line_iter) == Line("line3", 2, 12)
    line_iter.undo()
    assert next(line_iter) == Line("line3", 2, 12)
    line_iter.undo()
    assert next(line_iter) == Line("line3", 2, 12)
    assert next(line_iter) == Line("line4", 3, 18)
    assert next(line_iter, None) is None


def test_undo_last():

    line_iter = StringLineIterator(TEST_LINES)

    assert next(line_iter) == Line("line1", 0, 0)
    assert next(line_iter) == Line("line2", 1, 6)
    assert next(line_iter) == Line("line3", 2, 12)
    assert next(line_iter) == Line("line4", 3, 18)
    line_iter.undo()
    assert next(line_iter) == Line("line4", 3, 18)
    assert next(line_iter, None) is None
