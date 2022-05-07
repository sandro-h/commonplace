from dataclasses import dataclass


@dataclass
class ParseConfig:
    pass


@dataclass
class Line:
    content: str
    line_num: int
    offset: int
