import { addDays, addYears, endOfDay, getDay, getDaysInMonth, isAfter, isBefore, setDay } from 'date-fns'
import { Instance, isRecurringMoment, isSingleMoment, Moment, MomentDateTime, Recurrence, RecurrenceType, RecurringMoment, SingleMoment, WorkState } from './models'
import { epochWeek } from './util'

interface GenerateOptions {
    inclSubs?: boolean
    predicate?: (i: Instance) => boolean
}

export function generateInstances(moments: Moment[], start: Date, end: Date, options: GenerateOptions = { inclSubs: true }) {
    return moments.flatMap(m => generateInstancesOfMoment(m, start, end, options))
}

export function generateInstancesOfMoment(moment: Moment, start: Date, end: Date, options: GenerateOptions = { inclSubs: true }) {
    end = endOfDay(end)
    const instances: Instance[] = createInstances(moment, start, end).filter(i => !options.predicate || options.predicate(i))
    if (options.inclSubs === undefined || options.inclSubs) {
        instances.forEach(inst => {
            inst.subInstances = generateInstances(moment.subMoments, inst.start, inst.end, options)
        })
    }

    return instances
}

function createInstances(moment: Moment, start: Date, end: Date) {
    if (isSingleMoment(moment)) {
        return createSingleMomentInstances(moment as SingleMoment, start, end)
    }

    if (isRecurringMoment(moment)) {
        return createRecurringMomentInstances(moment as RecurringMoment, start, end)
    }

    return []
}

function createSingleMomentInstances(moment: SingleMoment, start: Date, end: Date) {
    const [instStart, instEnd] = intersect(start, end, moment.start, moment.end)
    if (!instStart || !instEnd) {
        return []
    }

    const endsInRange = moment.end !== null && !isAfter(moment.end.dt, instEnd)
    const inst = createInstance(moment, instStart, instEnd, endsInRange)
    return [inst]
}

function createRecurringMomentInstances(moment: RecurringMoment, start: Date, end: Date) {
    const instances = []
    for (const instStart of generateRecurring(moment.recurrence, start, end)) {
        instances.push(createInstance(moment, instStart, endOfDay(instStart), true))
    }
    return instances
}

function createInstance(moment: Moment, instStart: Date, instEnd: Date, endsInRange: boolean): Instance {
    return {
        name: moment.name,
        start: instStart,
        end: instEnd,
        timeOfDay: moment.timeOfDay?.dt ?? null,
        priority: moment.priority,
        category: moment.category,
        done: moment.workState === WorkState.DONE,
        workState: moment.workState,
        endsInRange,
        originDocPos: moment.docPos,
        subInstances: []
    }
}

/**
 * returns the start and end of the intersection of two Date ranges or (None,None) if they don't overlap.
 */
function intersect(start1: Date, end1: Date, start2: MomentDateTime | null, end2: MomentDateTime | null): [Date | null, Date | null] {
    const latestStart = latest(start1, start2?.dt ?? null)
    const earliestEnd = earliest(end1, end2?.dt ?? null)
    if (latestStart && earliestEnd && isBefore(earliestEnd, latestStart)) {
        // No overlap
        return [null, null]
    }

    return [latestStart, earliestEnd]
}

/**
 *  returns the earlier of two Dates. A nil time is considered infinitely late so won't be used if the other time is not nil.
 */
function earliest(t1: Date | null, t2: Date | null): Date | null {
    if (t1 === null) {
        // if t2 is also null, we return null
        return t2
    }

    if (t2 === null) {
        return t1
    }

    return isBefore(t1, t2) ? t1 : t2
}

/**
 * returns the later of two Dates. A nil time is considered infinitely early so won't be used if the other time is not nil.
 */
function latest(t1: Date | null, t2: Date | null): Date | null {
    if (t1 === null) {
        // if t2 is also None, we return None
        return t2
    }

    if (t2 === null) {
        return t1
    }
    return isAfter(t1, t2) ? t1 : t2
}

function* generateRecurring(recurrence: Recurrence, start: Date, end: Date): Generator<Date> {
    let cur = addDays(start, -1)
    while (true) {
        cur = nextRecurring(recurrence, cur)
        if (!isAfter(cur, end)) {
            yield cur
        }
        else {
            break
        }
    }
}

function nextRecurring(recurrence: Recurrence, after: Date) {
    switch (recurrence.recurrenceType) {
        case RecurrenceType.DAILY: return nextDaily(after, recurrence.refDate.dt)
        case RecurrenceType.WEEKLY: return nextWeekly(after, recurrence.refDate.dt)
        case RecurrenceType.BIWEEKLY: return nextNweekly(2, after, recurrence.refDate.dt)
        case RecurrenceType.TRIWEEKLY: return nextNweekly(3, after, recurrence.refDate.dt)
        case RecurrenceType.QUADRIWEEKLY: return nextNweekly(4, after, recurrence.refDate.dt)
        case RecurrenceType.MONTHLY: return nextMonthly(after, recurrence.refDate.dt)
        case RecurrenceType.YEARLY: return nextYearly(after, recurrence.refDate.dt)
        default: throw Error(`Unknown recurrence type ${recurrence.recurrenceType}`)
    }
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
function nextDaily(after: Date, _: Date) {
    return addDays(after, 1)
}

function nextWeekly(after: Date, refDate: Date) {
    let date = setDay(after, getDay(refDate))
    if (!isAfter(date, after)) {
        date = addDays(date, 7)
    }
    return date
}

function nextNweekly(nth: number, after: Date, refDate: Date) {
    let date = setDay(after, getDay(refDate))
    if (!isAfter(date, after)) {
        date = addDays(date, 7)
    }

    const offset = (epochWeek(date) - epochWeek(refDate)) % nth
    if (offset > 0) {
        date = addDays(date, 7 * (nth - offset))
    }
    else if (offset < 0) {
        date = addDays(date, -7 * offset)
    }

    return date
}

function nextMonthly(after: Date, refDate: Date) {
    let date = new Date(
        after.getFullYear(),
        after.getMonth(),
        Math.min(refDate.getDate(), getDaysInMonth(after)),
        0,
        0,
        0,
        0
    )

    if (!isAfter(date, after)) {
        const year = date.getMonth() === 11 ? date.getFullYear() + 1 : date.getFullYear()
        const month = (date.getMonth() + 1) % 12
        date = new Date(
            year,
            month,
            Math.min(refDate.getDate(), getDaysInMonth(new Date(year, month, 1))),
            0,
            0,
            0,
            0
        )
    }

    return date
}

function nextYearly(after: Date, refDate: Date) {
    let date = new Date(
        after.getFullYear(),
        refDate.getMonth(),
        refDate.getDate(),
        0,
        0,
        0,
        0
    )

    if (!isAfter(date, after)) {
        date = addYears(date, 1)
    }
    return date
}
