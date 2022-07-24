import { format } from 'date-fns'
import * as fs from 'fs'
import * as path from 'path'

export async function backup(file: string, backupDir: string, maxBackups = 3, fixedTime?: Date | null) {
    await fs.promises.mkdir(backupDir, { recursive: true })

    const [stem, suffix] = splitFileName(file)
    const now = fixedTime || new Date()
    const timestamp = format(now, 'yyyy-MM-dd_HH-mm-ss')
    const newBackup = path.join(backupDir, `${stem}.${timestamp}${suffix}`)

    await fs.promises.copyFile(file, newBackup, fs.constants.COPYFILE_EXCL)
    await pruneBackups(stem, backupDir, maxBackups)
}

async function pruneBackups(stem: string, backupDir: string, maxBackups: number) {
    const allBackups = await listBackupsNewestFirst(backupDir)
    await Promise.all(allBackups
        .filter(b => backupStem(b) === stem)
        .slice(maxBackups)
        .map(oldBackup => fs.promises.rm(oldBackup))
    )
}

export async function listBackupsNewestFirst(backupDir: string) {
    const allBackups = []

    const dir = await fs.promises.opendir(backupDir)
    for await (const dirent of dir) {
        if (dirent.isFile()) {
            allBackups.push(path.join(backupDir, dirent.name))
        }
    }

    allBackups.sort((a, b) => b.localeCompare(a))

    return allBackups
}

function splitFileName(file: string): [string, string] {
    const basename = path.basename(file)
    const m = basename.match(/^(.*)(\.[^.]*)$/)
    return m ? [m[1], m[2]] : [basename, '']
}

function backupStem(file: string): string {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const [stem, _] = splitFileName(file)
    return stem.replace(/\.[^.]+$/, '')
}
