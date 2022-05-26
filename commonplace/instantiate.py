from calendar import monthrange
from datetime import datetime, timedelta
from typing import List, Iterator
from commonplace.models import (Instance, Moment, MomentDateTime, Recurrence, RecurrenceType, RecurringMoment, SingleMoment,
                                WorkState)
from commonplace.util import epoch_week, with_end_of_day, with_weekday


def generate_instances(moments: List[Moment], start: datetime, end: datetime, incl_subs=True, predicate=None):
    return [i for m in moments for i in generate_instances_of_moment(m, start, end, incl_subs=incl_subs, predicate=predicate)]


def generate_instances_of_moment(moment: Moment, start: datetime, end: datetime, incl_subs=True, predicate=None):
    end = with_end_of_day(end)
    instances: List[Instance] = [i for i in create_instances(moment, start, end) if predicate is None or predicate(i)]
    if incl_subs:
        for inst in instances:
            inst.sub_instances = generate_instances(moment.sub_moments, inst.start, inst.end, incl_subs, predicate)

    return instances


def create_instances(moment: Moment, start: datetime, end: datetime):
    if isinstance(moment, SingleMoment):
        return create_single_moment_instances(moment, start, end)

    if isinstance(moment, RecurringMoment):
        return create_recurring_moment_instances(moment, start, end)

    return []


def create_single_moment_instances(moment: SingleMoment, start: datetime, end: datetime):
    inst_start, inst_end = intersect(start, end, moment.start, moment.end)
    if not inst_start:
        return []

    inst = create_instance(moment, inst_start, inst_end, ends_in_range=moment.end is not None and moment.end.dt <= inst_end)
    return [inst]


def create_recurring_moment_instances(moment: RecurringMoment, start: datetime, end: datetime):
    return [
        create_instance(moment, inst_start, with_end_of_day(inst_start), ends_in_range=True)
        for inst_start in generate_recurring(moment.recurrence, start, end)
    ]


def create_instance(moment: Moment, inst_start, inst_end, ends_in_range):
    return Instance(
        name=moment.name,
        start=inst_start,
        end=inst_end,
        time_of_day=moment.time_of_day.dt.time() if moment.time_of_day else None,
        priority=moment.priority,
        category=moment.category,
        done=moment.work_state == WorkState.DONE,
        work_state=moment.work_state,
        ends_in_range=ends_in_range,
        origin_doc_pos=moment.doc_pos,
    )


def intersect(start1: datetime, end1: datetime, start2: MomentDateTime | None, end2: MomentDateTime | None):
    """ returns the start and end of the intersection of two datetime ranges or (None,None) if they don't overlap. """
    upper_start = upper_bound(start1, start2.dt if start2 else None)
    lower_end = lower_bound(end1, end2.dt if end2 else None)
    if lower_end < upper_start:
        # No overlap
        return None, None

    return upper_start, lower_end


def lower_bound(t1: datetime, t2: datetime) -> datetime | None:  # pylint: disable=invalid-name
    """ returns the earlier of two datetimes. A nil time is considered infinitely late so won't be
    used if the other time is not nil. """
    if t1 is None:
        # if t2 is also None, we return None
        return t2

    if t2 is None:
        return t1

    return t1 if t1 < t2 else t2


def upper_bound(t1: datetime, t2: datetime) -> datetime | None:  # pylint: disable=invalid-name
    """ returns the later of two datetimes. A nil time is considered infinitely early so won't be
    used if the other time is not nil. """
    if t1 is None:
        # if t2 is also None, we return None
        return t2

    if t2 is None:
        return t1

    return t1 if t1 > t2 else t2


def generate_recurring(recurrence: Recurrence, start: datetime, end: datetime) -> Iterator[datetime]:
    cur = start - timedelta(days=1)
    while True:
        cur = next_recurring(recurrence, cur)
        if cur <= end:
            yield cur
        else:
            break


def next_recurring(recurrence: Recurrence, after: datetime):
    nexts = {
        RecurrenceType.DAILY: next_daily,
        RecurrenceType.WEEKLY: next_weekly,
        RecurrenceType.BI_WEEKLY: lambda a, rf: next_nweekly(2, a, rf),
        RecurrenceType.TRI_WEEKLY: lambda a, rf: next_nweekly(3, a, rf),
        RecurrenceType.QUADRI_WEEKLY: lambda a, rf: next_nweekly(4, a, rf),
        RecurrenceType.MONTHLY: next_monthly,
        RecurrenceType.YEARLY: next_yearly,
    }
    return nexts[recurrence.recurrence_type](after, recurrence.ref_date.dt)


def next_daily(after: datetime, _: datetime):
    return after + timedelta(days=1)


def next_weekly(after: datetime, ref_date: datetime):
    date = with_weekday(after, ref_date.weekday())
    if date <= after:
        date += timedelta(days=7)
    return date


def next_nweekly(nth: int, after: datetime, ref_date: datetime):
    date = with_weekday(after, ref_date.weekday())
    if date <= after:
        date += timedelta(days=7)

    offset = (epoch_week(date) - epoch_week(ref_date)) % nth
    if offset > 0:
        date += timedelta(days=7 * (nth - offset))
    elif offset < 0:
        date += timedelta(days=-7 * offset)

    return date


def next_monthly(after: datetime, ref_date: datetime):
    date = datetime(
        year=after.year,
        month=after.month,
        day=min(ref_date.day, last_day_of_month(after.year, after.month)),
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    ).astimezone(tz=None)

    if date <= after:
        year = date.year + 1 if date.month == 12 else date.year
        month = date.month % 12 + 1
        date = date.replace(
            year=year,
            month=month,
            day=min(ref_date.day, last_day_of_month(year, month)),
        )

    return date


def last_day_of_month(year, month):
    return monthrange(year, month)[1]


def next_yearly(after: datetime, ref_date: datetime):
    date = datetime(
        year=after.year,
        month=ref_date.month,
        day=ref_date.day,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    ).astimezone(tz=None)

    if date <= after:
        date = date.replace(year=date.year + 1)
    return date
