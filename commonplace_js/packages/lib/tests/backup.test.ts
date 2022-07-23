import { backup, listBackupsNewestFirst } from '../backup'
import * as tmp from 'tmp';
import * as path from 'path';
import * as fs from 'fs';
import { addSeconds, parse } from 'date-fns';

const DUMMY_CONTENT = "hello world"

test('creates backup', async () => {
    // Given
    const tmpDir = tmp.dirSync({ unsafeCleanup: true }).name
    const file = path.join(tmpDir, "todo.txt")
    const backupDir = path.join(tmpDir, "backups")

    await fs.promises.writeFile(file, DUMMY_CONTENT);

    // When
    await backup(file, backupDir)
    const backups = await listBackupsNewestFirst(backupDir)

    // Then
    expect(backups).toHaveLength(1)
    expect(load(backups[0])).toBe(DUMMY_CONTENT)
    expect(load(file)).toBe(DUMMY_CONTENT)
});

test('creates multiple backups', async () => {
    // Given
    const tmpDir = tmp.dirSync({ unsafeCleanup: true }).name
    const file = path.join(tmpDir, "todo.txt")
    const backupDir = path.join(tmpDir, "backups")

    // When
    const now = new Date();
    await fs.promises.writeFile(file, DUMMY_CONTENT);
    await backup(file, backupDir, 3, now);

    await fs.promises.writeFile(file, DUMMY_CONTENT + '2');
    await backup(file, backupDir, 3, addSeconds(now, 2));

    await fs.promises.writeFile(file, DUMMY_CONTENT + '3');
    await backup(file, backupDir, 3, addSeconds(now, 5));

    const backups = await listBackupsNewestFirst(backupDir)

    // Then
    expect(backups).toHaveLength(3)
    expect(load(backups[2])).toBe(DUMMY_CONTENT)
    expect(load(backups[1])).toBe(DUMMY_CONTENT + '2')
    expect(load(backups[0])).toBe(DUMMY_CONTENT + '3')
});

test('prunes backup', async () => {
    // Given
    const tmpDir = tmp.dirSync({ unsafeCleanup: true }).name
    const file = path.join(tmpDir, "todo.txt")
    const backupDir = path.join(tmpDir, "backups")

    await fs.promises.writeFile(file, DUMMY_CONTENT);

    await fs.promises.mkdir(backupDir, { recursive: true })
    await Promise.all([
        touch(path.join(backupDir, "todo.2022-06-11_15-00-30.txt")),
        touch(path.join(backupDir, "todo.2022-06-11_15-00-31.txt")),
        touch(path.join(backupDir, "todo.2022-06-11_15-00-32.txt")),
        touch(path.join(backupDir, "todo.2022-06-11_15-00-33.txt")),
        touch(path.join(backupDir, "todo-trash.2022-06-11_15-00-30.txt")),
    ])

    // When
    await backup(file, backupDir, 3, parse("2022-06-11_15-05-52", "yyyy-MM-dd_HH-mm-ss", new Date()))

    const backups = await listBackupsNewestFirst(backupDir)

    // Then
    expect(backups.map(b => path.basename(b))).toEqual([
        "todo.2022-06-11_15-05-52.txt",
        "todo.2022-06-11_15-00-33.txt",
        "todo.2022-06-11_15-00-32.txt",
        "todo-trash.2022-06-11_15-00-30.txt",
    ])
});

function load(file: string): string {
    return fs.readFileSync(file).toString()
}

async function touch(file: string) {
    return fs.promises.writeFile(file, "")
}
