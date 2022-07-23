import json
import os
import re

import pytest
from system_tests.models import Category, DocPosition

from system_tests.sys_test_util import (TESTDATA_DIR, dataclass_to_dict, dedent, request_parse)


@pytest.mark.parametrize(
    "content,expected_match",
    [
        ("[] foobar", "new"),
        ("[p] foobar", "in_progress"),
        ("[w] foobar", "waiting"),
        ("[x] foobar", "done"),
        ("[ x] foobar", "done"),
        ("[x ] foobar", "done"),
        ("[   x ] foobar", "done"),
        ("[\tx ] foobar", "done"),
        ("[ ] foobar", "new"),
        ("[ \t] foobar", "new"),
        ("[xp] foobar", None),
        ("[x foobar", None),
        ("x] foobar", None),
        ("x foobar", None),
    ],
)
def test_parse_mark(content, expected_match):
    # When
    result = request_parse(content)
    moments = result["moments"]
    moment = moments[0] if moments else None

    # Then
    if expected_match is None:
        assert moment is None, f"Should be None, got: {moment}"
    else:
        assert moment["work_state"] == expected_match


@pytest.mark.parametrize(
    "content,expected_category",
    [
        (
            """\
            ------------------
             a cat
            ------------------
            """,
            Category(name="a cat", doc_pos=DocPosition(1, 19, 6)),
        ),
        (
            """\
            ------------------
             a cat [blue]
            ------------------
            """,
            Category(name="a cat", color="blue", doc_pos=DocPosition(1, 19, 13)),
        ),
        (
            """\
            ------------------
             a cat!!
            ------------------
            """,
            Category(name="a cat", priority=2, doc_pos=DocPosition(1, 19, 8)),
        ),
        (
            """\
            ------------------
             a cat! [red]
            ------------------
            """,
            Category(name="a cat", priority=1, color="red", doc_pos=DocPosition(1, 19, 13)),
        ),
    ],
)
def test_parse_category(content, expected_category):
    # When
    result = request_parse(dedent(content))
    print(result)
    category = result["categories"][0]

    # Then
    assert category == dataclass_to_dict(expected_category)


@pytest.mark.golden_test("testdata/parse.golden.yml")
def test_full_parse(golden):
    # Given
    with open(os.path.join(TESTDATA_DIR, golden["input"]["todo_file"]), "r", encoding="utf8") as file:
        todo = file.read()

    # When
    data = request_parse(todo)
    pretty_data = json.dumps(data, indent=2, sort_keys=True)

    # Then
    assert remove_timezone_offset(pretty_data) == golden.out["output"]


def remove_timezone_offset(result):
    return re.sub(r"\+\d{2}:\d{2}", "", result)
