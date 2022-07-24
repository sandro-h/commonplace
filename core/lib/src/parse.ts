import { addDays, endOfDay, isValid, parse, setDay, startOfDay } from 'date-fns'
import { LineIterator, LineIteratorImpl, StringLineIterator } from './LineIterator'
import {
    Category, createTodos, getNow, Line, Moment, MomentDateTime, ParseConfig, Recurrence, RecurrenceType,
    RecurrenceWithoutDocPos,
    RecurringMoment, SingleMoment, Todos, WorkState
} from './models'
import { epochWeek, each } from './util'

interface ParseState {
    config: ParseConfig
    lineIter: LineIterator
    todos: Todos
}

export function parseMomentsString(content: string, config: ParseConfig): Todos {
    return parseMomentsLines(StringLineIterator(content), config)
}

export function parseMoments(lines: Iterator<string>, config: ParseConfig): Todos {
    return parseMomentsLines(new LineIteratorImpl(lines), config)
}

export function parseMomentsLines(lineIter: LineIterator, config: ParseConfig): Todos {
    const state: ParseState = { config, lineIter, todos: createTodos() }
    for (const line of each(state.lineIter)) {
        parseLine(line, state)
    }
    return state.todos
}

function nextLine(lineIter: LineIterator): Line | null {
    const { value, done } = lineIter.next()
    return done ? null : value
}

function parseLine(line: Line, state: ParseState) {
    if (isBlank(line.content)) {
        return
    }

    if (isCategoryDelimiter(line, state.config)) {
        parseCategoryBlock(state)
    }
    else if (line.content.startsWith(state.config.leftStateBracket)) {
        parseTopMomentBlock(line, state)
    }
}

function parseCategoryBlock(state: ParseState) {
    const catLine = nextLine(state.lineIter)
    if (catLine === null) {
        // Expected a category name after category delimiter
        return
    }

    const lineAfterCat = nextLine(state.lineIter)
    if (!isCategoryDelimiter(lineAfterCat, state.config)) {
        // Expected closing delimiter line
        return
    }

    state.todos.categories.push(parseCategory(catLine, state.config))
}

function parseCategory(line: Line, config: ParseConfig): Category {
    let color, content, priority
    [color, content] = parseCategoryColor(line.content);
    [priority, content] = parsePriority(content, config)
    return {
        name: content.trimStart(),
        color,
        priority,
        docPos: {
            lineNum: line.lineNum,
            offset: line.offset,
            length: line.content.length
        }
    }
}

function parseCategoryColor(content: string): [string, string] {
    const start = content.indexOf('[')

    if (start < 0 || !content.endsWith(']')) {
        return ['', content]
    }

    return [content.slice(start + 1, -1), content.slice(0, start).trim()]
}

function parsePriority(content: string, config: ParseConfig): [number, string] {
    let prio = 0
    for (; prio < content.length; prio++) {
        if (content[content.length - 1 - prio] !== config.priorityMark) {
            break
        }
    }

    return [prio, content.slice(0, content.length - prio).trim()]
}

function isCategoryDelimiter(line: Line | null, config: ParseConfig) {
    return line !== null && line.content.startsWith(config.categoryDelim)
}

function parseTopMomentBlock(line: Line, state: ParseState) {
    const mom = parseMomentBlock(line, line.content.trim(), state)
    if (!mom) {
        return
    }
    state.todos.moments.push(mom)
}

function parseMomentBlock(line: Line, lineContent: string, state: ParseState, indent = 0): Moment | null {
    const mom = parseMomentLine(line, lineContent, state.config)
    if (!mom) {
        return null
    }

    mom.category = state.todos.categories ? state.todos.categories[state.todos.categories.length - 1] : null
    parseCommentsAndSubMoments(mom, state, indent)
    return mom
}

function parseMomentLine(line: Line, lineContent: string, config: ParseConfig): Moment | null {
    let mom: Partial<Moment> | null;
    [mom, lineContent] = parseRecurringMoment(line, lineContent, config)
    if (!mom) {
        [mom, lineContent] = parseSingleMoment(line, lineContent, config)
    }

    let state
    [state, lineContent] = parseStateMark(lineContent, config)
    if (state === null) {
        return null
    }
    mom.workState = state;

    [mom.priority, lineContent] = parsePriority(lineContent, config)

    mom.name = lineContent
    mom.comments = []
    mom.subMoments = []

    return mom as Moment
}

function parseRecurringMoment(line: Line, lineContent: string, config: ParseConfig): [Partial<RecurringMoment> | null, string] {
    if (!lineContent.endsWith(config.rightDateBracket)) {
        return [null, lineContent]
    }

    const [recur, timeOfDay, newLineContent] = parseRecurrence(line, lineContent, config)
    if (!recur) {
        return [null, lineContent]
    }

    const mom: Partial<RecurringMoment> = {
        recurrence: recur,
        timeOfDay,
        docPos: {
            lineNum: line.lineNum,
            offset: line.offset,
            length: line.content.length
        }
    }

    return [mom, newLineContent]
}

function parseRecurrence(line: Line, lineContent: string, config: ParseConfig): [Recurrence | null, MomentDateTime | null, string] {
    const lbracketPos = lineContent.lastIndexOf(config.leftDateBracket)
    if (lbracketPos < 0) {
        return [null, null, lineContent]
    }

    const untrimmedPos = line.content.lastIndexOf(config.leftDateBracket) + 1
    let recurStr = lineContent.slice(lbracketPos + 1, -1)
    let timeOfDay
    [timeOfDay, recurStr] = parseTimeSuffix(recurStr, config)
    if (timeOfDay) {
        timeOfDay.docPos.offset += line.offset + untrimmedPos
    }

    let recurWithoutDocPos = null
    for (const parseFunc of [tryParseDaily, tryParseWeekly, tryParseNWeekly, tryParseMonthly, tryParseYearly]) {
        recurWithoutDocPos = parseFunc(recurStr, config)
        if (recurWithoutDocPos) {
            break
        }
    }

    if (!recurWithoutDocPos) {
        return [null, null, lineContent]
    }

    const recur = {
        ...recurWithoutDocPos,
        refDate: {
            ...recurWithoutDocPos.refDate,
            docPos: {
                lineNum: line.lineNum,
                offset: line.offset + untrimmedPos,
                length: recurStr.length
            }
        }
    }

    return [recur, timeOfDay, lineContent.slice(0, lbracketPos).trim()]
}

function tryParseDaily(content: string, config: ParseConfig): RecurrenceWithoutDocPos | null {
    if (!content.match(config.dailyPattern)) {
        return null
    }

    return {
        recurrenceType: RecurrenceType.DAILY,
        refDate: { dt: getNow(config) }
    }
}

function tryParseWeekly(content: string, config: ParseConfig): RecurrenceWithoutDocPos | null {
    const match = content.match(config.weeklyPattern)
    if (!match) {
        return null
    }

    const weekday = parseWeekday(match[1], config)
    if (weekday < 0) {
        return null
    }

    const refDate = setDay(getNow(config), weekday)
    return {
        recurrenceType: RecurrenceType.WEEKLY,
        refDate: { dt: startOfDay(refDate) }
    }
}

function parseWeekday(content: string, config: ParseConfig): number {
    return config.weekDays.indexOf(content.toLowerCase())
}

function tryParseNWeekly(content: string, config: ParseConfig): RecurrenceWithoutDocPos | null {
    const match = content.match(config.nWeeklyPattern)
    if (!match) {
        return null
    }

    const [nth, nthRecurType] = parseNth(match[1], config)
    if (!nthRecurType) {
        return null
    }

    const weekday = parseWeekday(match[2], config)
    if (weekday < 0) {
        return null
    }

    let refDate = setDay(getNow(config), weekday)
    const weekOffset = epochWeek(refDate) % nth
    refDate = addDays(refDate, -7 * weekOffset)
    return {
        recurrenceType: nthRecurType,
        refDate: { dt: startOfDay(refDate) }
    }
}

function parseNth(content: string, config: ParseConfig): [number, RecurrenceType | null] {
    switch (config.nths.indexOf(content.toLowerCase())) {
        case 0:
            return [2, RecurrenceType.BIWEEKLY]
        case 1:
            return [3, RecurrenceType.TRIWEEKLY]
        case 2:
            return [4, RecurrenceType.QUADRIWEEKLY]
        default:
            return [-1, null]
    }
}

function tryParseMonthly(content: string, config: ParseConfig): RecurrenceWithoutDocPos | null {
    const match = content.match(config.monthlyPattern)
    if (!match) {
        return null
    }

    const day = parseInt(match[1])
    if (isNaN(day)) {
        return null
    }

    const now = getNow(config)
    const refDate = new Date(now.getFullYear(), now.getMonth(), day)

    return {
        recurrenceType: RecurrenceType.MONTHLY,
        refDate: { dt: refDate }
    }
}

function tryParseYearly(content: string, config: ParseConfig): RecurrenceWithoutDocPos | null {
    const match = content.match(config.yearlyPattern)
    if (!match) {
        return null
    }

    const day = parseInt(match[1])
    const month = parseInt(match[2])
    if (isNaN(day) || isNaN(month)) {
        return null
    }

    const now = getNow(config)
    const refDate = new Date(now.getFullYear(), month - 1, day)
    return {
        recurrenceType: RecurrenceType.YEARLY,
        refDate: { dt: refDate }
    }
}

function parseSingleMoment(line: Line, lineContent: string, config: ParseConfig): [Partial<SingleMoment>, string] {
    let start = null
    let end = null
    let timeOfDay = null
    if (lineContent.endsWith(config.rightDateBracket)) {
        [start, end, timeOfDay, lineContent] = parseDateSuffix(line, lineContent, config)
    }

    if (end) {
        end.dt = endOfDay(end.dt)
    }

    return [
        {
            start,
            end,
            timeOfDay,
            docPos: {
                lineNum: line.lineNum,
                offset: line.offset,
                length: line.content.length
            }
        },
        lineContent
    ]
}

function parseDateSuffix(line: Line, lineContent: string, config: ParseConfig): [MomentDateTime | null, MomentDateTime | null, MomentDateTime | null, string] {
    const leftPos = lineContent.lastIndexOf(config.leftDateBracket)
    if (leftPos < 0) {
        return [null, null, null, lineContent]
    }

    const untrimmedPos = line.content.lastIndexOf(config.leftDateBracket) + 1
    let suffixStr = lineContent.slice(leftPos + 1, -1)
    let timeOfDay
    [timeOfDay, suffixStr] = parseTimeSuffix(suffixStr, config)
    finalizeDocPos(timeOfDay, line, untrimmedPos)

    suffixStr = suffixStr.trim()
    let start: MomentDateTime | null = null
    let end: MomentDateTime | null = null
    // Try all dashes as separator in case the date format uses dashes (e.g. 2015-12-24 - 2016-02-03)
    let dashOffset = 0
    let dashPos = suffixStr.indexOf('-')
    while (dashPos >= 0 && start === null) {
        [start, end] = parseDateRange(suffixStr, dashOffset + dashPos, config)
        if (start == null) {
            dashOffset += dashPos + 1
            dashPos = suffixStr.indexOf('-', dashOffset)
        }
    }

    if (!start) {
        start = parseDateSingle(suffixStr, config)
        if (start) {
            end = { ...start }
            end.docPos = { ...start.docPos }
        }
    }

    if (end) {
        end.dt = endOfDay(end.dt)
    }

    if (start || end) {
        finalizeDocPos(start, line, untrimmedPos)
        finalizeDocPos(end, line, untrimmedPos)
        return [start, end, timeOfDay, lineContent.slice(0, leftPos).trim()]
    }

    return [null, null, null, lineContent]
}

function parseDateRange(lineContent: string, dashPos: number, config: ParseConfig): [MomentDateTime | null, MomentDateTime | null] {
    let start: MomentDateTime | null = null
    let end: MomentDateTime | null = null
    const startStr = lineContent.slice(0, dashPos)
    const endStr = lineContent.slice(dashPos + 1)

    if (startStr) {
        const date = parseDate(startStr, config)
        if (!date) {
            return [null, null]
        }
        start = {
            dt: startOfDay(date),
            docPos: {
                lineNum: -1,
                offset: countStartWhitespaces(startStr),
                length: strippedLength(startStr)
            }
        }
    }

    if (endStr) {
        const date = parseDate(endStr, config)
        if (!date) {
            return [null, null]
        }
        end = {
            dt: endOfDay(date),
            docPos: {
                lineNum: -1,
                offset: startStr.length + 1 + countStartWhitespaces(endStr),
                length: strippedLength(endStr)
            }
        }
    }

    return [start, end]
}

function parseDateSingle(lineContent: string, config: ParseConfig): MomentDateTime | null {
    const date = parseDate(lineContent, config)

    if (!date) {
        return null
    }

    return {
        dt: startOfDay(date),
        docPos: {
            lineNum: -1,
            offset: countStartWhitespaces(lineContent),
            length: strippedLength(lineContent)
        }
    }
}

function parseTimeSuffix(lineContent: string, config: ParseConfig): [MomentDateTime | null, string] {
    const trimmed = lineContent.trim()
    const spacePos = trimmed.lastIndexOf(' ')
    if (spacePos < 0 || spacePos === trimmed.length - 1) {
        return [null, lineContent]
    }

    const timeStr = trimmed.slice(spacePos + 1)
    const timeOfDay = parseTime(timeStr, config)
    if (!timeOfDay) {
        return [null, lineContent]
    }

    const momTime = {
        dt: timeOfDay,
        docPos: {
            lineNum: -1,
            offset: spacePos + 1,
            length: timeStr.length
        }
    }

    return [momTime, lineContent.slice(0, spacePos)]
}

function finalizeDocPos(date: MomentDateTime | null, line: Line, offsetDelta: number) {
    if (date) {
        date.docPos.lineNum = line.lineNum
        date.docPos.offset += line.offset + offsetDelta
    }
}

function parseStateMark(lineContent: string, config: ParseConfig): [WorkState | null, string] {
    const match = config.stateMarkPattern.exec(lineContent)
    if (!match) {
        return [null, lineContent]
    }
    const leftover = lineContent.slice(match.index + match[0].length + 1).trim()
    return [config.stateMarks[match[1]] ?? WorkState.NEW, leftover]
}

function parseCommentsAndSubMoments(mom: Moment, state: ParseState, indent: number) {
    const nextIndent = indent + state.config.tabSize

    for (const line of each(state.lineIter)) {
        const [lineIndent, indentCharCnt] = countIndent(line.content, state.config.tabSize, nextIndent)

        if (lineIndent >= nextIndent) {
            parseSubLine(mom, line, line.content.slice(indentCharCnt), nextIndent, state)
        }
        else if (isBlank(line.content)) {
            if (mom.comments.length > 0) {
                // special case: treat empty line between comments as a comment
                mom.comments.push(
                    {
                        content: '',
                        docPos: { lineNum: line.lineNum, offset: line.offset, length: 0 }
                    })
            }
        }
        // Otherwise just ignore the empty line
        else {
            // "Unconsume" the line since it is probably meant for a parent moment up the recursion stack
            state.lineIter.undo()
            break
        }
    }

    // Remove trailing empty comments
    while (mom.comments.length > 0 && mom.comments[mom.comments.length - 1].content === '') {
        mom.comments = mom.comments.slice(0, -1)
    }
}

function parseSubLine(mom: Moment, line: Line, lineContent: string, indent: number, state: ParseState) {
    if (lineContent.startsWith(state.config.leftStateBracket)) {
        const subMom = parseMomentBlock(line, lineContent, state, indent)
        if (subMom) {
            mom.subMoments.push(subMom)
            return
        }
    }

    // If not a sub moment, assume it's a comment
    const [, indentCharCnt] = countIndent(line.content, state.config.tabSize, indent)
    mom.comments.push(
        {
            content: lineContent,
            docPos: {
                lineNum: line.lineNum,
                offset: line.offset + indentCharCnt,
                length: lineContent.length
            }
        })
}

function parseDate(content: string, config: ParseConfig): Date | null {
    const stripped = content.trim()
    for (const fmt of config.dateFormats) {
        const dt = parse(stripped, fmt, new Date())
        if (isValid(dt)) {
            return dt
        }
    }

    return null
}

function parseTime(content: string, config: ParseConfig): Date | null {
    const stripped = content.trim()
    const dt = parse(stripped, config.timeFormat, new Date())
    return isValid(dt) ? dt : null
}

/**
 * counts the whitespace indent at the start of the string up to maxIndent.
 * Spaces count as 1, Tabs count as tabSize indentation.
 * Returns the indentation value and the actual number of whitespace characters.
*/
function countIndent(content: string, tabSize: number, maxIndent: number): [number, number] {
    let indent = 0
    let cnt = 0
    for (const char of content) {
        if (char === '\t') {
            indent += tabSize
            cnt += 1
        }
        else if (char === ' ') {
            indent += 1
            cnt += 1
        }
        else {
            break
        }

        if (indent >= maxIndent) {
            break
        }
    }

    return [indent, cnt]
}

function isBlank(content: string) {
    return !content.trim()
}

function countStartWhitespaces(content: string) {
    for (let i = 0; i < content.length; i++) {
        if (!/\s/.test(content[i])) {
            return i
        }
    }

    return content.length
}

function strippedLength(content: string) {
    return content.trim().length
}
