import os

import pytest

from system_tests.sys_test_util import TESTDATA_DIR, dedent, request_fold, request_format, request_outline


@pytest.mark.parametrize(
    "content,expected_format",
    [
        # Categories
        (
            """
            ------------------
            cat1
            ------------------

            [] bla

            ------------------
            cat2
            ------------------

            [] foo
            """,
            """\
            20,24,cat
            72,76,cat
            45,51,mom
            97,103,mom
            """,
        ),
        # Comments
        (
            """\
            [] bla1
                [x] sub
            [] bla2
                comments
                comments
            [x] bla3
                comments
                comments
            """,
            """\
            0,7,mom
            8,19,mom.done
            20,27,mom
            54,62,mom.done
            67,88,com.done
            """,
        ),
        # Due soon. Note fixed date is 2022-06-05
        (
            """\
            [] bla1 (7.6.22)
            [] bla2 (7.6.22-15.6.22)
            [] bla3 (7.6.22-16.6.22)
            [] bla4 (every day)
            [] bla5 (4.6.22)
            """,
            """\
            0,16,mom.until2
            9,15,date
            17,41,mom.until10
            26,32,date
            33,40,date
            42,66,mom
            51,57,date
            58,65,date
            67,86,mom.until0
            76,85,date
            87,103,mom
            96,102,date
            """,
        ),
        # Optimized format with comments after subcomments
        (
            """
            [] bla1
                [] bla2
                comments
                comments

            [] bla3
            """,
            """\
            1,20,mom
            48,55,mom
            """,
        ),
        # State styles
        (
            """
            [] new
            [p] in progress
                [] sub should not get state style
            [w] waiting
                [] sub should not get state style
            [x] done
                [] sub should get done style
            [p] due soon overrides state style (07.06.22)
            [p] priority progress!
            [w] priority waiting!
            """,
            """\
            1,7,mom
            8,23,mom.inProgress
            24,61,mom
            62,73,mom.waiting
            74,111,mom
            112,153,mom.done
            154,199,mom.until2
            190,198,date
            200,222,mom.inProgress.priority
            223,244,mom.waiting.priority
            """,
        ),
    ],
)
def test_format(content, expected_format):
    # When
    fmt = request_format(dedent(content))

    # Then
    assert fmt == dedent(expected_format)


def test_due_soon_daylight_savings():
    # Scenario:
    # It's the 23.3
    # Daylight savings time happens on 31.3
    # The moment date 3.4. will be seen as 263 hours away, instead of 264 (=11 days)

    # Given
    content = """
        [] bla1 (3.4.19)
        [] bla2 (2.4.19)
    """

    # When
    fmt = request_format(dedent(content), fixed_time="2019-03-23")

    # Then
    assert fmt == dedent("""\
    1,17,mom
    10,16,date
    18,34,mom.until10
    27,33,date
    """)


@pytest.mark.golden_test("testdata/format.golden.yml")
def test_full_format(golden):
    # Given
    with open(os.path.join(TESTDATA_DIR, golden["input"]["todo_file"]), "rb") as file:
        # Remove carrier returns to get same offsets on windows and linux.
        todo = file.read().decode("utf8").replace("\r", "")

    # When
    fmt = request_format(todo)

    # Then
    assert fmt == golden.out["output"]


@pytest.mark.golden_test("testdata/format_trash.golden.yml")
def test_format_trash(golden):
    # Given
    with open(os.path.join(TESTDATA_DIR, golden["input"]["todo_file"]), "rb") as file:
        # Remove carrier returns to get same offsets on windows and linux.
        todo = file.read().decode("utf8").replace("\r", "")

    # When
    fmt = request_format(todo, format_type="trash")

    # Then
    assert fmt == golden.out["output"]


@pytest.mark.parametrize(
    "content,expected_fold",
    [
        (
            """\
            [] bla1
            [] bla2
            [x] bla3
            """,
            "",
        ),
        (
            """\
            [] bla1
                [x] sub
                    comments
                    blaa
            [] bla2
                comments
                comments
                comments
                comments
                comments
            [x] bla3
                comments
                comments
            """,
            """\
            0-3
            4-9
            10-12
            """,
        ),
    ],
)
def test_fold(content, expected_fold):
    # When
    fmt = request_fold(dedent(content))

    # Then
    assert fmt == dedent(expected_fold)


@pytest.mark.golden_test("testdata/outline.golden.yml")
def test_outline(golden):
    # Given
    with open(os.path.join(TESTDATA_DIR, golden["input"]["todo_file"]), "rb") as file:
        todo = file.read()

    # When
    fmt = request_outline(todo.decode("utf8"))

    # Then
    assert fmt == golden.out["output"]


@pytest.mark.golden_test("testdata/outline_trash.golden.yml")
def test_outline_trash(golden):
    # Given
    with open(os.path.join(TESTDATA_DIR, golden["input"]["todo_file"]), "rb") as file:
        todo = file.read()

    # When
    fmt = request_outline(todo.decode("utf8"), format_type="trash")

    # Then
    assert fmt == golden.out["output"]
