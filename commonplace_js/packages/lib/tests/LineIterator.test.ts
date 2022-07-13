import { StringLineIterator } from '../LineIterator'

const TEST_LINES = `\
line1
line2
line3
line4\
`;

test('reads lines', () => {
    const lineIter = StringLineIterator(TEST_LINES)

    expect(lineIter.next()).toStrictEqual({ value: { content: 'line1', lineNum: 0, offset: 0 }, done: false })
    expect(lineIter.next()).toStrictEqual({ value: { content: 'line2', lineNum: 1, offset: 6 }, done: false })
    expect(lineIter.next()).toStrictEqual({ value: { content: 'line3', lineNum: 2, offset: 12 }, done: false })
    expect(lineIter.next()).toStrictEqual({ value: { content: 'line4', lineNum: 3, offset: 18 }, done: false })
    expect(lineIter.next()).toStrictEqual({ value: null, done: true })
});

test('reads empty last line', () => {

    const lines = `\
line1
line2
line3
line4
`;

    const lineIter = StringLineIterator(lines)

    expect(lineIter.next()).toStrictEqual({ value: { content: 'line1', lineNum: 0, offset: 0 }, done: false })
    expect(lineIter.next()).toStrictEqual({ value: { content: 'line2', lineNum: 1, offset: 6 }, done: false })
    expect(lineIter.next()).toStrictEqual({ value: { content: 'line3', lineNum: 2, offset: 12 }, done: false })
    expect(lineIter.next()).toStrictEqual({ value: { content: 'line4', lineNum: 3, offset: 18 }, done: false })
    expect(lineIter.next()).toStrictEqual({ value: { content: '', lineNum: 4, offset: 24 }, done: false })
    expect(lineIter.next()).toStrictEqual({ value: null, done: true })
});

test('reads empty last line', () => {

    const lines = `\
line1
line2
line3
line4
`;

    const lineIter = StringLineIterator(lines)

    expect(lineIter.next()).toStrictEqual({ value: { content: 'line1', lineNum: 0, offset: 0 }, done: false })
    expect(lineIter.next()).toStrictEqual({ value: { content: 'line2', lineNum: 1, offset: 6 }, done: false })
    expect(lineIter.next()).toStrictEqual({ value: { content: 'line3', lineNum: 2, offset: 12 }, done: false })
    expect(lineIter.next()).toStrictEqual({ value: { content: 'line4', lineNum: 3, offset: 18 }, done: false })
    expect(lineIter.next()).toStrictEqual({ value: { content: '', lineNum: 4, offset: 24 }, done: false })
    expect(lineIter.next()).toStrictEqual({ value: null, done: true })
});

test('handles carrier returns', () => {
    const lines = 'line1\r\nline2\r\nline3\r\nline4'

    const lineIter = StringLineIterator(lines)

    expect(lineIter.next()).toStrictEqual({ value: { content: 'line1', lineNum: 0, offset: 0 }, done: false })
    expect(lineIter.next()).toStrictEqual({ value: { content: 'line2', lineNum: 1, offset: 7 }, done: false })
    expect(lineIter.next()).toStrictEqual({ value: { content: 'line3', lineNum: 2, offset: 14 }, done: false })
    expect(lineIter.next()).toStrictEqual({ value: { content: 'line4', lineNum: 3, offset: 21 }, done: false })
    expect(lineIter.next()).toStrictEqual({ value: null, done: true })
});

test('can undo', () => {
    const lineIter = StringLineIterator(TEST_LINES)

    expect(lineIter.next()).toStrictEqual({ value: { content: 'line1', lineNum: 0, offset: 0 }, done: false })
    expect(lineIter.next()).toStrictEqual({ value: { content: 'line2', lineNum: 1, offset: 6 }, done: false })
    lineIter.undo()
    expect(lineIter.next()).toStrictEqual({ value: { content: 'line2', lineNum: 1, offset: 6 }, done: false })
    expect(lineIter.next()).toStrictEqual({ value: { content: 'line3', lineNum: 2, offset: 12 }, done: false })
    lineIter.undo()
    expect(lineIter.next()).toStrictEqual({ value: { content: 'line3', lineNum: 2, offset: 12 }, done: false })
    expect(lineIter.next()).toStrictEqual({ value: { content: 'line4', lineNum: 3, offset: 18 }, done: false })
    expect(lineIter.next()).toStrictEqual({ value: null, done: true })
});

test('can undo the same line repeatedly', () => {
    const lineIter = StringLineIterator(TEST_LINES)

    expect(lineIter.next()).toStrictEqual({ value: { content: 'line1', lineNum: 0, offset: 0 }, done: false })
    expect(lineIter.next()).toStrictEqual({ value: { content: 'line2', lineNum: 1, offset: 6 }, done: false })
    expect(lineIter.next()).toStrictEqual({ value: { content: 'line3', lineNum: 2, offset: 12 }, done: false })
    lineIter.undo()
    expect(lineIter.next()).toStrictEqual({ value: { content: 'line3', lineNum: 2, offset: 12 }, done: false })
    lineIter.undo()
    expect(lineIter.next()).toStrictEqual({ value: { content: 'line3', lineNum: 2, offset: 12 }, done: false })
    lineIter.undo()
    expect(lineIter.next()).toStrictEqual({ value: { content: 'line3', lineNum: 2, offset: 12 }, done: false })
    expect(lineIter.next()).toStrictEqual({ value: { content: 'line4', lineNum: 3, offset: 18 }, done: false })
    expect(lineIter.next()).toStrictEqual({ value: null, done: true })
});

test('can undo last line', () => {
    const lineIter = StringLineIterator(TEST_LINES)

    expect(lineIter.next()).toStrictEqual({ value: { content: 'line1', lineNum: 0, offset: 0 }, done: false })
    expect(lineIter.next()).toStrictEqual({ value: { content: 'line2', lineNum: 1, offset: 6 }, done: false })
    expect(lineIter.next()).toStrictEqual({ value: { content: 'line3', lineNum: 2, offset: 12 }, done: false })
    expect(lineIter.next()).toStrictEqual({ value: { content: 'line4', lineNum: 3, offset: 18 }, done: false })
    lineIter.undo()
    expect(lineIter.next()).toStrictEqual({ value: { content: 'line4', lineNum: 3, offset: 18 }, done: false })
    expect(lineIter.next()).toStrictEqual({ value: null, done: true })
});
