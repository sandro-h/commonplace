import re


def dedent(content):
    """Removes the base indentation from a multi-line string.
    Allows to properly indent multiline strings in these tests for better readability."""
    parts = content.split("\n")
    indent = len(re.match(r"^(\s*)", parts[0]).group(1))
    return "\n".join([p[indent:] for p in parts])
