import { addDays, compareAsc, endOfDay, endOfWeek, format, startOfDay, startOfWeek } from 'date-fns'
import { generateInstances } from './instantiate'
import { Instance, Preview, PreviewCategory, PreviewOverview, Todos, WorkState, PreviewInstance, CalendarEntry } from './models'

export function previewMoments(todos: Todos, fixedTime?: Date | null): Preview {
    const now = fixedTime || new Date()
    const [today, week] = compileReminders(todos, now)

    return {
        overview: compileTopLevelMoments(todos),
        today,
        week,
        calendar: toCalendarEntries(week)
    }
}

function compileTopLevelMoments(todos: Todos) {
    const overview: PreviewOverview = { categories: [] }
    let category: PreviewCategory | undefined
    todos.moments
        .filter(m => m.workState !== WorkState.DONE)
        .forEach(m => {
            const catName = m.category?.name || '_none'
            if (!category || catName !== category.name) {
                category = { name: catName, moments: [] }
                overview.categories.push(category)
            }
            category.moments.push({
                name: m.name,
                workState: m.workState,
                docPos: m.docPos
            })
        })
    return overview
}

function compileReminders(todos: Todos, now: Date) {
    const today = compileMomentsEndingInRange(todos, startOfDay(now), endOfDay(now))
    const week = compileMomentsEndingInRange(todos, startOfWeek(now, { weekStartsOn: 1 }), endOfWeek(now, { weekStartsOn: 1 }))
    return [
        flattenReminders(today),
        flattenReminders(week)
    ]
}

function compileMomentsEndingInRange(todos: Todos, start: Date, end: Date): Instance[] {
    const instances = filterMomentsEndingInRange(
        generateInstances(todos.moments, start, end, { predicate: inst => !inst.done })
    )

    instances.sort((a, b) => compareAsc(a.start, b.start))
    return instances
}

function filterMomentsEndingInRange(instances: Instance[]): Instance[] {
    const res: Instance[] = []
    instances.forEach(inst => {
        const subsEndingInRange = filterMomentsEndingInRange(inst.subInstances)
        if (subsEndingInRange.length || inst.endsInRange) {
            res.push({
                ...inst,
                subInstances: subsEndingInRange
            })
        }
    })

    return res
}

function flattenReminders(instances: Instance[], parentPath = ''): PreviewInstance[] {
    return instances.flatMap(inst => {
        const flattened: PreviewInstance[] = []

        if (inst.endsInRange) {
            // eslint-disable-next-line @typescript-eslint/no-unused-vars
            const { subInstances, ...previewInst } = { ...inst }
            previewInst.name = parentPath + inst.name
            flattened.push(previewInst)
        }

        return flattened.concat(flattenReminders(inst.subInstances, `${parentPath}${inst.name}/`))
    })
}

function toCalendarEntries(instances: PreviewInstance[]): CalendarEntry[] {
    const sortedInstances = [...instances]
    sortedInstances.sort((a, b) => priority(b) - priority(a))

    return sortedInstances.map(inst => ({
        title: inst.name + (inst.timeOfDay ? format(inst.timeOfDay, ' HH:mm') : ''),
        start: format(inst.start, 'yyyy-MM-dd'),
        // +1 because fullcalendar is non-inclusive
        end: format(addDays(inst.end, 1), 'yyyy-MM-dd'),
        color: inst.category?.color ?? null
    }))
}

function priority(mom: PreviewInstance) {
    return Math.max(mom.priority, mom.category?.priority ?? 0)
}
