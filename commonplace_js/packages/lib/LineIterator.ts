import { Line } from './models';

export class LineIterator implements Iterator<Line> {

    private lines: Iterator<string>
    private lineNumber: number
    private offset: number
    private lastLine: string | null
    private undoing: boolean

    constructor(lines: Iterator<string>) {
        this.lines = lines
        this.lineNumber = 0
        this.offset = 0
        this.lastLine = null
        this.undoing = false
    }

    undo() {
        if (this.lastLine === null) {
            throw new Error('Cannot undo before reading at least one line')
        }
        this.undoing = false
    }

    next(): IteratorResult<Line, any> {
        let line: string | null
        if (this.undoing) {
            line = this.lastLine
            this.lineNumber -= 1
            this.offset -= line!.length
            this.undoing = false
        }
        else {
            const next = this.lines.next()
            line = next.done ? null : next.value
            // Explicitly return last line if empty, since we'd lose this information because
            // we strip newlines in the returned content
            if (next.done && this.lastLine !== null && this.lastLine.endsWith("\n")) {
                line = ""
            }
        }

        if (line === null) {
            return { done: true, value: null }
        }

        const result: Line = {
            content: line.trimEnd(),
            lineNum: this.lineNumber,
            offset: this.offset,
        };

        this.lastLine = line
        this.lineNumber += 1
        this.offset += line.length

        return { done: false, value: result }
    }
}
