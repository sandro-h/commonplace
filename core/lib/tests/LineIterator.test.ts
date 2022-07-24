import { StringLineIterator } from '../src/LineIterator'

const TEST_LINES = `\
line1
line2
line3
line4\
`

const EXP_LINE1 = { content: 'line1', lineNum: 0, offset: 0, originalLineLength: 6 }
const EXP_LINE2 = { content: 'line2', lineNum: 1, offset: 6, originalLineLength: 6 }
const EXP_LINE3 = { content: 'line3', lineNum: 2, offset: 12, originalLineLength: 6 }
const EXP_LINE4 = { content: 'line4', lineNum: 3, offset: 18, originalLineLength: 5 }

test('reads lines', () => {
  const lineIter = StringLineIterator(TEST_LINES)

  expect(lineIter.next()).toStrictEqual({ value: EXP_LINE1, done: false })
  expect(lineIter.next()).toStrictEqual({ value: EXP_LINE2, done: false })
  expect(lineIter.next()).toStrictEqual({ value: EXP_LINE3, done: false })
  expect(lineIter.next()).toStrictEqual({ value: EXP_LINE4, done: false })
  expect(lineIter.next()).toStrictEqual({ value: null, done: true })
})

test('reads empty last line', () => {
  const lines = `\
line1
line2
line3
line4
`

  const lineIter = StringLineIterator(lines)

  expect(lineIter.next()).toStrictEqual({ value: EXP_LINE1, done: false })
  expect(lineIter.next()).toStrictEqual({ value: EXP_LINE2, done: false })
  expect(lineIter.next()).toStrictEqual({ value: EXP_LINE3, done: false })
  expect(lineIter.next()).toStrictEqual({ value: { ...EXP_LINE4, originalLineLength: 6 }, done: false })
  expect(lineIter.next()).toStrictEqual({ value: { content: '', lineNum: 4, offset: 24, originalLineLength: 0 }, done: false })
  expect(lineIter.next()).toStrictEqual({ value: null, done: true })
})

test('handles carrier returns', () => {
  const lines = 'line1\r\nline2\r\nline3\r\nline4'

  const lineIter = StringLineIterator(lines)

  expect(lineIter.next()).toStrictEqual({ value: { content: 'line1', lineNum: 0, offset: 0, originalLineLength: 7 }, done: false })
  expect(lineIter.next()).toStrictEqual({ value: { content: 'line2', lineNum: 1, offset: 7, originalLineLength: 7 }, done: false })
  expect(lineIter.next()).toStrictEqual({ value: { content: 'line3', lineNum: 2, offset: 14, originalLineLength: 7 }, done: false })
  expect(lineIter.next()).toStrictEqual({ value: { content: 'line4', lineNum: 3, offset: 21, originalLineLength: 5 }, done: false })
  expect(lineIter.next()).toStrictEqual({ value: null, done: true })
})

test('can undo', () => {
  const lineIter = StringLineIterator(TEST_LINES)

  expect(lineIter.next()).toStrictEqual({ value: EXP_LINE1, done: false })
  expect(lineIter.next()).toStrictEqual({ value: EXP_LINE2, done: false })
  lineIter.undo()
  expect(lineIter.next()).toStrictEqual({ value: EXP_LINE2, done: false })
  expect(lineIter.next()).toStrictEqual({ value: EXP_LINE3, done: false })
  lineIter.undo()
  expect(lineIter.next()).toStrictEqual({ value: EXP_LINE3, done: false })
  expect(lineIter.next()).toStrictEqual({ value: EXP_LINE4, done: false })
  expect(lineIter.next()).toStrictEqual({ value: null, done: true })
})

test('can undo the same line repeatedly', () => {
  const lineIter = StringLineIterator(TEST_LINES)

  expect(lineIter.next()).toStrictEqual({ value: EXP_LINE1, done: false })
  expect(lineIter.next()).toStrictEqual({ value: EXP_LINE2, done: false })
  expect(lineIter.next()).toStrictEqual({ value: EXP_LINE3, done: false })
  lineIter.undo()
  expect(lineIter.next()).toStrictEqual({ value: EXP_LINE3, done: false })
  lineIter.undo()
  expect(lineIter.next()).toStrictEqual({ value: EXP_LINE3, done: false })
  lineIter.undo()
  expect(lineIter.next()).toStrictEqual({ value: EXP_LINE3, done: false })
  expect(lineIter.next()).toStrictEqual({ value: EXP_LINE4, done: false })
  expect(lineIter.next()).toStrictEqual({ value: null, done: true })
})

test('can undo last line', () => {
  const lineIter = StringLineIterator(TEST_LINES)

  expect(lineIter.next()).toStrictEqual({ value: EXP_LINE1, done: false })
  expect(lineIter.next()).toStrictEqual({ value: EXP_LINE2, done: false })
  expect(lineIter.next()).toStrictEqual({ value: EXP_LINE3, done: false })
  expect(lineIter.next()).toStrictEqual({ value: EXP_LINE4, done: false })
  lineIter.undo()
  expect(lineIter.next()).toStrictEqual({ value: EXP_LINE4, done: false })
  expect(lineIter.next()).toStrictEqual({ value: null, done: true })
})
