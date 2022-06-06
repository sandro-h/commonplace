from system_tests.sys_test_util import request_clean, request_trash

TEST_INPUT = """\
[] foo
[x] bar
    some commet
    [] bar1
    [] bar2
[] gib
    [x] ja
[x] haba
    comments1
    comments2
    comments3
[] yo
"""


def test_clean(tmp_path):
    # Given

    todo_file = tmp_path / "todo.txt"
    with open(todo_file, "w", encoding="utf8") as file:
        file.write(TEST_INPUT)

    # When
    request_clean(todo_file)

    with open(todo_file, "r", encoding="utf8") as file:
        updated_content = file.read()

    # Then
    assert updated_content == """\
[] foo
[] gib
    [x] ja
[] yo
[x] bar
    some commet
    [] bar1
    [] bar2
[x] haba
    comments1
    comments2
    comments3
"""


def test_trash(tmp_path):
    # Given
    todo_file = tmp_path / "todo.txt"
    trash_file = tmp_path / "trash.txt"

    with open(todo_file, "w", encoding="utf8") as file:
        file.write(TEST_INPUT)

    # When
    request_trash(todo_file, trash_file)

    with open(todo_file, "r", encoding="utf8") as file:
        updated_content = file.read()
    with open(trash_file, "r", encoding="utf8") as file:
        trash_content = file.read()

    # Then
    assert updated_content == """\
[] foo
[] gib
    [x] ja
[] yo
"""
    assert trash_content == """\
------------------
  Trash from 05.06.2022 00:00:00
------------------
[x] bar
    some commet
    [] bar1
    [] bar2
[x] haba
    comments1
    comments2
    comments3
"""
