import { getUnixTime } from "date-fns"

/**
 * returns the number of weeks passed since January 1, 1970 UTC.
 * Note this does not mean it's aligned for weekdays, i.e. the Monday after
 * Sunday does not necessary have a higher EpochWeek number. 
 */
export function epochWeek(date: Date): number {
    return Math.floor(getUnixTime(date) / 604800);
}

export function inLocalTimezone(date: Date): Date {
    return new Date(date.getTime() - date.getTimezoneOffset() * 60000);
}