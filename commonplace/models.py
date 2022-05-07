from dataclasses import dataclass, field
from typing import List


@dataclass
class ParseConfig:

    category_delim: str = "------"
    priority_mark: str = "!"


@dataclass
class Line:
    content: str
    line_num: int
    offset: int


@dataclass
class DocPosition:
    line_num: int
    offset: int
    length: int


@dataclass
class Category:
    name: str
    doc_pos: DocPosition
    color: str = ""
    priority: int = 0


@dataclass
class Todos:
    categories: List[Category] = field(default_factory=list)
