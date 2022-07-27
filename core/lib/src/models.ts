export const EOF_OFFSET = -1

export enum WorkState {
    NEW = 'new',
    WAITING = 'waiting',
    IN_PROGRESS = 'inProgress',
    DONE = 'done',
}

export interface ParseConfig {

    categoryDelim: string
    priorityMark: string
    tabSize: number
    leftStateBracket: string
    rightStateBracket: string
    leftDateBracket: string
    rightDateBracket: string
    dateFormats: string[]
    timeFormat: string
    stateMarks: Record<string, WorkState>
    stateMarkPattern: RegExp
    weekDays: string[]
    dailyPattern: RegExp
    weeklyPattern: RegExp
    nths: string[]
    nWeeklyPattern: RegExp
    monthlyPattern: RegExp
    yearlyPattern: RegExp
    fixedTime: Date | null
}

export function getNow(config: ParseConfig): Date {
    return config.fixedTime ? config.fixedTime : new Date()
}

export function createParseConfig(): ParseConfig {
    const defaultConfig = {
        categoryDelim: '------',
        priorityMark: '!',
        tabSize: 4,
        leftStateBracket: '[',
        rightStateBracket: ']',
        leftDateBracket: '(',
        rightDateBracket: ')',
        dateFormats: ['dd.MM.yy', 'dd.M.yy', 'd.M.yy', 'dd.MM.yyyy', 'd.M.yyyy', 'd.MM.yyyy'],
        timeFormat: 'HH:mm',
        stateMarks: {
            x: WorkState.DONE,
            w: WorkState.WAITING,
            p: WorkState.IN_PROGRESS
        },
        stateMarkPattern: /^\[\s*([xwp]?)\s*\]/,
        weekDays: ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'],
        dailyPattern: /(every day|today)/i,
        weeklyPattern: /every (monday|tuesday|wednesday|thursday|friday|saturday|sunday)/i,
        nths: ['2nd', '3rd', '4th'],
        nWeeklyPattern: /every (2nd|3rd|4th) (monday|tuesday|wednesday|thursday|friday|saturday|sunday)/i,
        monthlyPattern: /every (\d{1,2})\.?$/i,
        yearlyPattern: /every (\d{1,2})\.(\d{1,2})\.?$/i,
        fixedTime: null
    }

    return { ...defaultConfig }
}

export interface Line {
    content: string
    lineNum: number
    offset: number
    originalLineLength: number
}

export interface DocPosition {
    lineNum: number
    offset: number
    length: number
}

export interface Category {
    name: string
    docPos: DocPosition
    color: string
    priority: number
}

export interface Comment {
    content: string
    docPos: DocPosition
}

export interface MomentDateTime {
    dt: Date
    docPos: DocPosition
}

export interface Moment {
    name: string
    comments: Comment[]
    subMoments: Moment[]
    workState: WorkState
    priority: number
    category: Category | null
    timeOfDay: MomentDateTime | null
    docPos: DocPosition
}

export interface SingleMoment extends Moment {
    start: MomentDateTime | null
    end: MomentDateTime | null
}

export function isSingleMoment(mom: Moment) {
    return 'start' in mom
}

export enum RecurrenceType {
    DAILY = 'daily',
    WEEKLY = 'weekly',
    MONTHLY = 'monthly',
    YEARLY = 'yearly',
    BIWEEKLY = 'biweekly',
    TRIWEEKLY = 'triweekly',
    QUADRIWEEKLY = 'quadriweekly',
}

export interface Recurrence {
    recurrenceType: RecurrenceType
    refDate: MomentDateTime
}

export interface RecurrenceWithoutDocPos extends Omit<Recurrence, 'refDate'> {
    refDate: Omit<MomentDateTime, 'docPos'>
}

export interface RecurringMoment extends Moment {
    recurrence: Recurrence
}

export function isRecurringMoment(mom: Moment) {
    return 'recurrence' in mom
}

export interface Todos {
    categories: Category[]
    moments: Moment[]
}

export function createTodos() {
    return {
        categories: [],
        moments: []
    }
}

export interface Instance {
    name: string
    start: Date
    end: Date
    endsInRange: boolean
    originDocPos: DocPosition
    timeOfDay: Date | null
    priority: number
    category: Category | null
    done: boolean
    workState: WorkState
    subInstances: Instance[]
}

export interface Outline {
    name: string
    startLine: number
    endLine: number
    detail: string
}

export enum EditType {
    INSERT,
    DELETE
}

export interface Edit {
    type: EditType
}

export interface InsertEdit extends Edit {
    offset: number
    content: string
}

export interface DeleteEdit extends Edit {
    startOffset: number
    endOffset: number
}

export interface CalendarEntry {
    title: string
    start: string
    end: string
    color: string | null
}

export type PreviewMoment = Pick<Moment, 'name' | 'workState' | 'docPos'>

export type PreviewInstance = Omit<Instance, 'subInstances'>

export interface PreviewCategory {
    name: string
    moments: PreviewMoment[]
}

export interface PreviewOverview {
    categories: PreviewCategory[]
}

export interface Preview {
    today: PreviewInstance[]
    week: PreviewInstance[]
    overview: PreviewOverview
    calendar: CalendarEntry[]
}
