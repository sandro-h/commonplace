import pytest
from commonplace.models import Category, Instance
from commonplace.util import with_end_of_day

from system_tests.sys_test_util import (dataclass_to_dict, dedent, parse_dmy, request_instances)


@pytest.mark.parametrize(
    "content,start,end,expected_instances",
    [
        # target range contained in moment range
        (
            "[] bla (18.06.2016-25.06.2016)",
            "20.06.2016",
            "22.06.2016",
            [
                Instance(
                    name="bla",
                    start=parse_dmy("20.06.2016"),
                    end=with_end_of_day(parse_dmy("22.06.2016")),
                    ends_in_range=False,
                )
            ],
        ),
        # moment range contained in target range
        (
            "[] bla (18.06.2016-25.06.2016)",
            "01.06.2016",
            "01.08.2016",
            [
                Instance(
                    name="bla",
                    start=parse_dmy("18.06.2016"),
                    end=with_end_of_day(parse_dmy("25.06.2016")),
                    ends_in_range=True,
                )
            ],
        ),
        # unbounded moment
        (
            "[] bla",
            "20.06.2016",
            "22.06.2016",
            [
                Instance(
                    name="bla",
                    start=parse_dmy("20.06.2016"),
                    end=with_end_of_day(parse_dmy("22.06.2016")),
                    ends_in_range=False,
                )
            ],
        ),
        # out of range
        (
            "[] bla (18.06.2016-25.06.2016)",
            "01.07.2016",
            "13.07.2016",
            [],
        ),
        # with categories
        (
            dedent("""\
                ------------------
                 a cat
                ------------------
                [] 1
                    [] 1.1
                ------------------
                another cat
                ------------------
                [] 2\
                """),
            "01.06.2016",
            "01.08.2016",
            [
                Instance(name="1",
                         start=parse_dmy("01.06.2016"),
                         end=with_end_of_day(parse_dmy("01.08.2016")),
                         ends_in_range=False,
                         category=Category(name="a cat"),
                         sub_instances=[
                             Instance(
                                 name="1.1",
                                 start=parse_dmy("01.06.2016"),
                                 end=with_end_of_day(parse_dmy("01.08.2016")),
                                 ends_in_range=False,
                                 category=Category(name="a cat"),
                             ),
                         ]),
                Instance(
                    name="2",
                    start=parse_dmy("01.06.2016"),
                    end=with_end_of_day(parse_dmy("01.08.2016")),
                    ends_in_range=False,
                    category=Category(name="another cat"),
                ),
            ],
        ),
        # children
        (
            dedent("""\
            [] 1 (18.06.2016-25.06.2016)
                [] 1.1 (20.06.2016-23.06.2016)
                [] 1.2 (18.06.2016-19.06.2016)\
            """),
            "01.06.2016",
            "01.08.2016",
            [
                Instance(
                    name="1",
                    start=parse_dmy("18.06.2016"),
                    end=with_end_of_day(parse_dmy("25.06.2016")),
                    ends_in_range=True,
                    sub_instances=[
                        Instance(
                            name="1.1",
                            start=parse_dmy("20.06.2016"),
                            end=with_end_of_day(parse_dmy("23.06.2016")),
                            ends_in_range=True,
                        ),
                        Instance(
                            name="1.2",
                            start=parse_dmy("18.06.2016"),
                            end=with_end_of_day(parse_dmy("19.06.2016")),
                            ends_in_range=True,
                        ),
                    ],
                ),
            ],
        ),
        # children cut off by parent
        (
            dedent("""\
            [] 1 (18.06.2016-25.06.2016)
                [] 1.1 (20.06.2016-30.06.2016)
                [] 1.2 (01.07.2016-05.07.2016)\
            """),
            "01.06.2016",
            "01.08.2016",
            [
                Instance(
                    name="1",
                    start=parse_dmy("18.06.2016"),
                    end=with_end_of_day(parse_dmy("25.06.2016")),
                    ends_in_range=True,
                    sub_instances=[
                        Instance(
                            name="1.1",
                            start=parse_dmy("20.06.2016"),
                            end=with_end_of_day(parse_dmy("25.06.2016")),
                            ends_in_range=False,
                        ),
                    ],
                ),
            ],
        ),
        # children cut off by range
        (
            dedent("""\
            [] 1 (18.06.2016-25.06.2016)
                [] 1.1 (20.06.2016-23.06.2016)\
            """),
            "01.06.2016",
            "21.06.2016",
            [
                Instance(
                    name="1",
                    start=parse_dmy("18.06.2016"),
                    end=with_end_of_day(parse_dmy("21.06.2016")),
                    ends_in_range=False,
                    sub_instances=[
                        Instance(
                            name="1.1",
                            start=parse_dmy("20.06.2016"),
                            end=with_end_of_day(parse_dmy("21.06.2016")),
                            ends_in_range=False,
                        ),
                    ],
                ),
            ],
        ),
        # recurring every day
        (
            "[] bla (every day)",
            "20.06.2016",
            "22.06.2016",
            [
                Instance(
                    name="bla", start=parse_dmy("20.06.2016"), end=with_end_of_day(parse_dmy("20.06.2016")), ends_in_range=True),
                Instance(
                    name="bla", start=parse_dmy("21.06.2016"), end=with_end_of_day(parse_dmy("21.06.2016")), ends_in_range=True),
                Instance(
                    name="bla", start=parse_dmy("22.06.2016"), end=with_end_of_day(parse_dmy("22.06.2016")), ends_in_range=True),
            ],
        ),
        # recurring every week
        (
            "[] bla (every friday)",
            "14.05.2022",
            "30.05.2022",
            [
                Instance(
                    name="bla", start=parse_dmy("20.05.2022"), end=with_end_of_day(parse_dmy("20.05.2022")), ends_in_range=True),
                Instance(
                    name="bla", start=parse_dmy("27.05.2022"), end=with_end_of_day(parse_dmy("27.05.2022")), ends_in_range=True),
            ],
        ),
        # recurring every 2nd week
        (
            "[] bla (every 2nd friday)",
            "01.05.2022",
            "31.05.2022",
            [
                Instance(
                    name="bla", start=parse_dmy("13.05.2022"), end=with_end_of_day(parse_dmy("13.05.2022")), ends_in_range=True),
                Instance(
                    name="bla", start=parse_dmy("27.05.2022"), end=with_end_of_day(parse_dmy("27.05.2022")), ends_in_range=True),
            ],
        ),
        # recurring every 3rd week
        (
            "[] bla (every 3rd friday)",
            "01.05.2022",
            "30.06.2022",
            [
                Instance(
                    name="bla", start=parse_dmy("20.05.2022"), end=with_end_of_day(parse_dmy("20.05.2022")), ends_in_range=True),
                Instance(
                    name="bla", start=parse_dmy("10.06.2022"), end=with_end_of_day(parse_dmy("10.06.2022")), ends_in_range=True),
            ],
        ),
        # recurring every 4th week
        (
            "[] bla (every 4th friday)",
            "01.05.2022",
            "30.06.2022",
            [
                Instance(
                    name="bla", start=parse_dmy("13.05.2022"), end=with_end_of_day(parse_dmy("13.05.2022")), ends_in_range=True),
                Instance(
                    name="bla", start=parse_dmy("10.06.2022"), end=with_end_of_day(parse_dmy("10.06.2022")), ends_in_range=True),
            ],
        ),
        # recurring every month
        (
            "[] bla (every 23.)",
            "1.06.2016",
            "30.07.2016",
            [
                Instance(
                    name="bla", start=parse_dmy("23.06.2016"), end=with_end_of_day(parse_dmy("23.06.2016")), ends_in_range=True),
                Instance(
                    name="bla", start=parse_dmy("23.07.2016"), end=with_end_of_day(parse_dmy("23.07.2016")), ends_in_range=True),
            ],
        ),
        # recurring every year
        (
            "[] bla (every 23.6.)",
            "1.06.2016",
            "30.07.2017",
            [
                Instance(
                    name="bla", start=parse_dmy("23.06.2016"), end=with_end_of_day(parse_dmy("23.06.2016")), ends_in_range=True),
                Instance(
                    name="bla", start=parse_dmy("23.06.2017"), end=with_end_of_day(parse_dmy("23.06.2017")), ends_in_range=True),
            ],
        ),
        # recurring not in range
        (
            "[] bla (every 23.)",
            "20.06.2016",
            "22.06.2016",
            [],
        ),
        # recurring children
        (
            dedent("""\
            [] 1 (18.06.2016-25.06.2016)
                [] 1.1 (every 20.)
                [] 1.2 (every day)
            """),
            "01.06.2016",
            "20.06.2016",
            [
                Instance(
                    name="1",
                    start=parse_dmy("18.06.2016"),
                    end=with_end_of_day(parse_dmy("20.06.2016")),
                    ends_in_range=False,
                    sub_instances=[
                        Instance(
                            name="1.1",
                            start=parse_dmy("20.06.2016"),
                            end=with_end_of_day(parse_dmy("20.06.2016")),
                            ends_in_range=True,
                        ),
                        Instance(
                            name="1.2",
                            start=parse_dmy("18.06.2016"),
                            end=with_end_of_day(parse_dmy("18.06.2016")),
                            ends_in_range=True,
                        ),
                        Instance(
                            name="1.2",
                            start=parse_dmy("19.06.2016"),
                            end=with_end_of_day(parse_dmy("19.06.2016")),
                            ends_in_range=True,
                        ),
                        Instance(
                            name="1.2",
                            start=parse_dmy("20.06.2016"),
                            end=with_end_of_day(parse_dmy("20.06.2016")),
                            ends_in_range=True,
                        ),
                    ],
                ),
            ],
        ),
        (
            dedent("""\
            [] 1 (every 20.)
                [] 1.1 (every 20.6)
                [] 1.2 (20.7.2016)
                [] 1.3 (21.6.2016)
            """),
            "01.06.2016",
            "30.07.2016",
            [
                Instance(name="1",
                         start=parse_dmy("20.06.2016"),
                         end=with_end_of_day(parse_dmy("20.06.2016")),
                         ends_in_range=True,
                         sub_instances=[
                             Instance(
                                 name="1.1",
                                 start=parse_dmy("20.06.2016"),
                                 end=with_end_of_day(parse_dmy("20.06.2016")),
                                 ends_in_range=True,
                             ),
                         ]),
                Instance(name="1",
                         start=parse_dmy("20.07.2016"),
                         end=with_end_of_day(parse_dmy("20.07.2016")),
                         ends_in_range=True,
                         sub_instances=[
                             Instance(
                                 name="1.2",
                                 start=parse_dmy("20.07.2016"),
                                 end=with_end_of_day(parse_dmy("20.07.2016")),
                                 ends_in_range=True,
                             ),
                         ]),
            ],
        ),
        ("[] bla (21.06.2016 13:15)", "20.06.2016", "22.06.2016", [
            Instance(
                name="bla",
                start=parse_dmy("21.06.2016"),
                end=with_end_of_day(parse_dmy("21.06.2016")),
                ends_in_range=True,
                time_of_day="13:15:00",
            ),
        ])
    ],
)
def test_instantiate(content, start, end, expected_instances):
    # When
    result = request_instances(content, start, end)

    # Then
    assert [without_doc_pos(r) for r in result] == [without_doc_pos(dataclass_to_dict(i)) for i in expected_instances]


def without_doc_pos(inst: dict):
    del inst["origin_doc_pos"]
    if inst.get("category"):
        del inst["category"]["doc_pos"]
    for sub in inst["sub_instances"]:
        without_doc_pos(sub)
    return inst
