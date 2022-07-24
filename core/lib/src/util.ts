import { getUnixTime, minutesToHours } from 'date-fns'
import { Moment } from './models'

/**
 * returns the number of weeks passed since January 1, 1970 UTC.
 * Note this does not mean it's aligned for weekdays, i.e. the Monday after
 * Sunday does not necessary have a higher EpochWeek number.
 */
export function epochWeek(date: Date): number {
  return Math.floor(getUnixTime(date) / 604800)
}

export function inLocalTimezone(date: Date): Date {
  return new Date(date.getTime() - date.getTimezoneOffset() * 60000)
}

export function isoTimezoneOffset(date: Date): string {
  const offsetMinutes = -date.getTimezoneOffset()
  const sign = offsetMinutes < 0 ? '-' : '+'
  const hours = minutesToHours(offsetMinutes) + ''
  const minutes = (offsetMinutes % 60) + ''
  return `${sign}${hours.padStart(2, '0')}:${minutes.padStart(2, '0')}`
}

export function getBottomLine(mom: Moment): number {
  return Math.max(
    mom.docPos.lineNum,
    mom.comments.length > 0 ? mom.comments[mom.comments.length - 1].docPos.lineNum : -1,
    mom.subMoments.length > 0 ? getBottomLine(mom.subMoments[mom.subMoments.length - 1]) : -1
  )
}

export function withNewline(content: string): string {
  if (!content) {
    return content
  }

  return content + (content.endsWith('\n') ? '' : '\n')
}

export function* each<T>(iter: Iterator<T>): Generator<T> {
  for (let next = iter.next(); !next.done; next = iter.next()) {
    yield next.value
  }
}

export function listFromIterator<T>(iter: Iterator<T>): T[] {
  const res = []
  for (const line of each(iter)) {
    res.push(line)
  }
  return res
}
