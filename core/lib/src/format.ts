import { addDays, differenceInDays, differenceInHours, startOfDay } from 'date-fns'
import { generateInstancesOfMoment } from './instantiate'
import { Moment, Todos, WorkState, SingleMoment, isSingleMoment, isRecurringMoment, RecurringMoment, DocPosition, Outline } from './models'
import { getBottomLine } from './util'

export const TODO_FORMAT = 'todo'
export const TRASH_FORMAT = 'trash'
const CAT_STYLE = 'cat'
const MOM_STYLE = 'mom'
const COM_STYLE = 'com'
const DATE_STYLE = 'date'
const TIME_STYLE = 'time'
const DONE_SUFFIX = '.done'
const PRIORITY_SUFFIX = '.priority'
const UNTIL_SUFFIX = '.until'

export interface FormatStyle {
    start: number
    end: number
    style: string
}

interface FormatState {
    rawContent: string
    styles: FormatStyle[]
    lastStyle?: FormatStyle
    fixedTime: Date | null
}

export function formatTodos(todos: Todos, rawContent: string, formatType: string = TODO_FORMAT, fixedTime: Date | null = null): FormatStyle[] {
    const state: FormatState = { rawContent, fixedTime, styles: [] }

    todos.categories.forEach(cat => addFormatLine(state, CAT_STYLE, cat.docPos))

    todos.moments.forEach(mom => {
        if (formatType === TODO_FORMAT) {
            formatMoment(state, mom)
        }
        else if (formatType === TRASH_FORMAT) {
            formatTrashMoment(state, mom)
        }
        else {
            throw Error(`Unknown format '${formatType}'`)
        }
    })

    if (state.lastStyle) {
        flushLastStyle(state)
    }

    return state.styles
}

function formatMoment(state: FormatState, mom: Moment, parentDone = false) {
    let style = MOM_STYLE
    const done = parentDone || mom.workState === WorkState.DONE
    if (done) {
        style += DONE_SUFFIX
    }
    else {
        style += formatDueSoon(mom, state.fixedTime)
        if (mom.priority > 0) {
            style += PRIORITY_SUFFIX
        }
    }

    addFormatLine(state, style, mom.docPos)

    if (done) {
        mom.comments.forEach(com => addFormatLine(state, COM_STYLE + DONE_SUFFIX, com.docPos))
    }
    else {
        formatDates(state, mom)
    }

    mom.subMoments.forEach(sub => formatMoment(state, sub, done))
}

function formatTrashMoment(state: FormatState, mom: Moment) {
    addFormatLine(state, MOM_STYLE, mom.docPos)
    formatDates(state, mom)
    mom.subMoments.forEach(sub => formatTrashMoment(state, sub))
}

function formatDates(state: FormatState, mom: Moment) {
    if (isSingleMoment(mom)) {
        const singleMom = mom as SingleMoment
        if (singleMom.start) {
            addFormatLine(state, DATE_STYLE, singleMom.start.docPos)
        }
        if (singleMom.end && (!singleMom.start || singleMom.end.docPos !== singleMom.start.docPos)) {
            addFormatLine(state, DATE_STYLE, singleMom.end.docPos)
        }
    }
    else if (isRecurringMoment(mom)) {
        addFormatLine(state, DATE_STYLE, (mom as RecurringMoment).recurrence.refDate.docPos)
    }

    if (mom.timeOfDay) {
        addFormatLine(state, TIME_STYLE, mom.timeOfDay.docPos)
    }
}

function formatDueSoon(mom: Moment, fixedTime: Date | null) {
    // Due until 10 (n-1) days in the future
    const cutoff = 11
    const today = startOfDay(fixedTime || new Date())
    const nDaysFromToday = addDays(today, cutoff)
    const nRealHours = differenceInHours(nDaysFromToday, today)
    const instances = generateInstancesOfMoment(mom, today, nDaysFromToday, false)
    let earliest = cutoff
    instances.forEach(inst => {
        // We need to compare hours here because of daylight saving time.
        // Instead of 264h (=11 days) it might only be 263h or 265h,
        // which would lead to the wrong number of days calculated.
        if (differenceInHours(inst.end, today) < nRealHours) {
            const dueDays = differenceInDays(inst.end, today)
            if (dueDays < earliest) {
                earliest = dueDays
            }
        }
    })

    if (earliest < cutoff) {
        return `${UNTIL_SUFFIX}${earliest}`
    }

    return ''
}

function addFormatLine(state: FormatState, style: string, pos: DocPosition) {
    if (state.lastStyle && style === state.lastStyle.style && onlyWhitespaceBetween(state.lastStyle.end, pos.offset, state.rawContent)) {
        state.lastStyle.end = pos.offset + pos.length
    }
    else {
        if (state.lastStyle) {
            flushLastStyle(state)
        }
        state.lastStyle = {
            start: pos.offset,
            end: pos.offset + pos.length,
            style
        }
    }
}

function flushLastStyle(state: FormatState) {
    state.styles.push(state.lastStyle!)
    state.lastStyle = undefined
}

function onlyWhitespaceBetween(start: number, end: number, rawContent: string) {
    for (let i = start; i < end; i++) {
        if (!/\s/.test(rawContent[i])) {
            return false
        }
    }
    return true
}

export function foldTodos(todos: Todos): number[][] {
    return todos.moments
        .map(mom => [mom.docPos.lineNum, getBottomLine(mom)])
        .filter(([start, end]) => end > start)
}

export function outlineTodos(todos: Todos, rawContent: string, formatType = TODO_FORMAT): Outline[] {
    return todos.moments
        .filter(mom => formatType !== TODO_FORMAT || mom.workState !== WorkState.DONE)
        .map(mom => outline(mom, rawContent))
}

function outline(mom: Moment, rawContent: string): Outline {
    let detail = ''
    if (isSingleMoment(mom)) {
        const singleMom = mom as SingleMoment
        if (singleMom.start) {
            detail += extract(rawContent, singleMom.start.docPos)
        }
        if (singleMom.end && (!singleMom.start || singleMom.end.docPos?.offset !== singleMom.start.docPos?.offset)) {
            detail += ' - ' + extract(rawContent, singleMom.end.docPos)
        }
    }
    else if (isRecurringMoment(mom)) {
        detail += extract(rawContent, (mom as RecurringMoment).recurrence.refDate.docPos)
    }

    if (mom.timeOfDay) {
        detail += ' ' + extract(rawContent, mom.timeOfDay.docPos)
    }

    return {
        name: mom.name,
        startLine: mom.docPos.lineNum,
        endLine: getBottomLine(mom),
        detail
    }
}

function extract(content: string, docPos: DocPosition): string {
    return content.slice(docPos.offset, docPos.offset + docPos.length)
}
