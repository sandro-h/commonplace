import pytest
from commonplace.models import Category, DocPosition, ParseConfig
from commonplace.parse import parse_moments_string
from tests.test_util import dedent


@pytest.mark.parametrize(
    "content,category",
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
def test_parse_category(content, category):
    todos = parse_moments_string(dedent(content), ParseConfig())

    assert todos.categories == [category]
