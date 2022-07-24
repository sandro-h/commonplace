import { Line } from './models'

export function* splitLikeFile(content: string) {
  let prev: string | null = null
  for (const line of content.split(/(\n)/)) {
    if (prev === null) {
      prev = line
    }
    else {
      yield prev + '\n'
      prev = null
    }
  }

  if (prev) { // deliberately also ignoring empty string
    yield prev
  }
}

export interface LineIterator extends Iterator<Line> {
  undo(): void
}

export class LineIteratorImpl implements LineIterator {
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
    this.undoing = true
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
      if (next.done && this.lastLine !== null && this.lastLine.endsWith('\n')) {
        line = ''
      }
    }

    if (line === null) {
      return { done: true, value: null }
    }

    const result: Line = {
      content: line.trimEnd(),
      lineNum: this.lineNumber,
      offset: this.offset,
      originalLineLength: line.length
    }

    this.lastLine = line
    this.lineNumber += 1
    this.offset += line.length

    return { done: false, value: result }
  }
}

export class ExistingLineIterator implements LineIterator {
  private lines: Line[]
  private index: number
  private undoing: boolean

  constructor(lines: Line[]) {
    this.lines = lines
    this.index = 0
    this.undoing = false
  }

  undo() {
    if (this.index === 0) {
      throw new Error('Cannot undo before reading at least one line')
    }
    if (this.undoing) {
      // Mimic same behavior as LineIteratorImpl: can only undo last read line
      return
    }
    this.index--
    this.undoing = true
  }

  next(): IteratorResult<Line, any> {
    this.undoing = false

    if (this.index >= this.lines.length) {
      return { done: true, value: null }
    }

    return { done: false, value: this.lines[this.index++] }
  }
}

export function StringLineIterator(content: string): LineIterator {
  return new LineIteratorImpl(splitLikeFile(content))
}
