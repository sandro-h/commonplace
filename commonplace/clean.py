from datetime import datetime
from typing import List, Tuple
from commonplace.line_iterator import StringLineIterator, each_line
from commonplace.models import Moment, ParseConfig, WorkState
from commonplace.parse import parse_moments_string


def clean_done_moments(todo_file, parse_config: ParseConfig):
    updated_content, deleted_content = _clean_done_moments(todo_file, parse_config)

    with open(todo_file, "w", encoding="utf8") as file:  # NOSONAR: path injection - localhost only, file args only in dev mode
        file.write(with_newline(updated_content) + with_newline(deleted_content))


def trash_done_moments(todo_file, trash_file, parse_config: ParseConfig, fixed_time=None):
    updated_content, deleted_content = _clean_done_moments(todo_file, parse_config)

    trash_time = fixed_time if fixed_time else datetime.now()
    with open(trash_file, "a", encoding="utf8") as file:  # NOSONAR: path injection - localhost only, file args only in dev mode
        file.write(f"""\
------------------
  Trash from {trash_time.strftime("%d.%m.%Y %H:%M:%S")}
------------------
""")
        file.write(with_newline(deleted_content))

    with open(todo_file, "w", encoding="utf8") as file:  # NOSONAR: path injection - localhost only, file args only in dev mode
        file.write(with_newline(updated_content))


def _clean_done_moments(todo_file, parse_config: ParseConfig):
    with open(todo_file, "r", encoding="utf8") as file:  # NOSONAR: path injection - localhost only, file args only in dev mode
        content = file.read()

    todos = parse_moments_string(content, parse_config)
    done_top_moments = [m for m in todos.moments if m.work_state == WorkState.DONE]

    return delete_moments(content, done_top_moments)


def delete_moments(content: str, to_delete: List[Moment]) -> Tuple[str, str]:
    updated_content = ""
    deleted_content = ""
    to_delete_index = 0
    prev_line_was_deleted = False

    for line in each_line(StringLineIterator(content)):
        delete, to_delete_index = decide_delete(line, to_delete, to_delete_index, prev_line_was_deleted)

        if delete:
            deleted_content += ("\n" if deleted_content else "") + line.content
        else:
            updated_content += ("\n" if updated_content else "") + line.content

        prev_line_was_deleted = delete

    return updated_content, deleted_content


def decide_delete(line, to_delete, to_delete_index, prev_line_was_deleted):
    del_range = get_line_range(to_delete[to_delete_index]) if to_delete_index < len(to_delete) else None

    delete = del_range and del_range[0] <= line.line_num <= del_range[1]
    delete = delete or prev_line_was_deleted and line.content.strip() == ""

    if del_range and line.line_num == del_range[1]:
        to_delete_index += 1

    return delete, to_delete_index


def get_line_range(mom: Moment):
    return (mom.doc_pos.line_num, get_bottom_line(mom))


def get_bottom_line(mom: Moment):
    return max(
        mom.doc_pos.line_num,
        mom.comments[-1].doc_pos.line_num if mom.comments else -1,
        get_bottom_line(mom.sub_moments[-1]) if mom.sub_moments else -1,
    )


def with_newline(content):
    if not content:
        return content
    return content + ("\n" if content[-1] != "\n" else "")
