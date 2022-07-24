import { format } from 'date-fns'
import { ExistingLineIterator, StringLineIterator } from './LineIterator'
import { createParseConfig, Edit, EditType, EOF_OFFSET, InsertEdit, Line, ParseConfig, WorkState } from './models'
import { parseMomentsLines } from './parse'
import { getBottomLine, listFromIterator } from './util'

export function cleanDoneMoments(content: string, parseConfig?: ParseConfig): Edit[] {
    const lines = listFromIterator(StringLineIterator(content))
    const todos = parseMomentsLines(new ExistingLineIterator(lines), parseConfig || createParseConfig())
    const doneTopMoments = todos.moments.filter(m => m.workState === WorkState.DONE)

    return doneTopMoments.flatMap(mom => {
        let bottom = getBottomLine(mom)
        let bottomWithTrailingLines = bottom
        while (bottomWithTrailingLines + 1 < lines.length && lines[bottomWithTrailingLines + 1].content === '') {
            bottomWithTrailingLines++
        }
        if (bottomWithTrailingLines > bottom) {
            // Include one empty line
            bottom += 1
        }

        return [
            { type: EditType.INSERT, offset: endOffset(lines[lines.length - 1]), content: content.slice(mom.docPos.offset, endOffset(lines[bottom])) },
            { type: EditType.DELETE, startOffset: mom.docPos.offset, endOffset: endOffset(lines[bottomWithTrailingLines]) }
        ]
    })
}

export function trashDoneMoments(content: string, parseConfig?: ParseConfig, fixedTime?: Date | null): [Edit[], Edit[]] {
    const edits = cleanDoneMoments(content, parseConfig)
    const todoEdits = edits.filter(e => e.type === EditType.DELETE)
    const trashEdits = edits.filter(e => e.type === EditType.INSERT)

    const trashTime = fixedTime || new Date()
    const trashHeader = `\
------------------
  Trash from ${format(trashTime, 'dd.MM.yyyy HH:mm:ss')}
------------------
`
    trashEdits.unshift({ type: EditType.INSERT, offset: EOF_OFFSET, content: trashHeader } as InsertEdit)
    trashEdits.forEach(e => {
        (e as InsertEdit).offset = EOF_OFFSET
    })

    return [todoEdits, trashEdits]
}

function endOffset(line: Line) {
    return line.offset + line.originalLineLength
}
