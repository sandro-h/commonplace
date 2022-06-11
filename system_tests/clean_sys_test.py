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


def test_clean(test_app_todo_dir):
    # Given

    todo_file = test_app_todo_dir / "todo.txt"
    with open(todo_file, "w", encoding="utf8") as file:
        file.write(TEST_INPUT)

    # When
    request_clean()

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


def test_trash(test_app_todo_dir):
    # Given
    todo_file = test_app_todo_dir / "todo.txt"
    trash_file = test_app_todo_dir / "todo-trash.txt"

    with open(todo_file, "w", encoding="utf8") as file:
        file.write(TEST_INPUT)

    # When
    request_trash()

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
