from datetime import datetime, timedelta, timezone

from commonplace.models import Moment


def with_start_of_day(date: datetime) -> datetime:
    return date.replace(hour=0, minute=0, second=0, microsecond=0)


def with_end_of_day(date: datetime) -> datetime:
    return date.replace(hour=23, minute=59, second=59, microsecond=999999)


def with_weekday(date: datetime, weekday: int) -> datetime:
    return date + timedelta(days=_with_golang_weekdays(weekday) - _with_golang_weekdays(date.weekday()))


def _with_golang_weekdays(weekday):
    """ rearrange weekday from Python Monday=0...Sunday=6 to Golang Sunday=0...Saturday=6 """
    # only really needed for system tests so we get exact same reference date
    return (weekday + 1) % 7


def epoch_week(date: datetime) -> int:
    """ returns the number of weeks passed since January 1, 1970 UTC.
        Note this does not mean it's aligned for weekdays, i.e. the Monday after
        Sunday does not necessary have a higher EpochWeek number. """

    return int(int(date.astimezone(timezone.utc).timestamp()) / 604800)


def parse_ymd(date_str: str) -> datetime:
    return datetime.strptime(date_str, "%Y-%m-%d") if date_str else None


def parse_ymd_hms(date_str: str) -> datetime:
    return datetime.strptime(date_str, "%Y-%m-%d_%H-%M-%S") if date_str else None


def format_ymd(date: datetime) -> str:
    return date.strftime("%Y-%m-%d")


def get_bottom_line(mom: Moment):
    return max(
        mom.doc_pos.line_num,
        mom.comments[-1].doc_pos.line_num if mom.comments else -1,
        get_bottom_line(mom.sub_moments[-1]) if mom.sub_moments else -1,
    )
