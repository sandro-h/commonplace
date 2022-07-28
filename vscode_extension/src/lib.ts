import {
    cleanDoneMoments, createParseConfig, DeleteEdit, Edit, EditType, EOF_OFFSET, foldTodos, FormatStyle, formatTodos, InsertEdit, Outline, outlineTodos,
    parseMomentsString, TODO_FORMAT, trashDoneMoments, TRASH_FORMAT, backup, previewMoments
} from '@commonplace/lib'
import * as vscode from 'vscode'
import * as path from 'path'
import * as fs from 'fs'
import { trashLangId } from './util'
import { Todos } from '@commonplace/lib/models'

interface CacheEntry {
    version: number;
    promise?: Promise<Object>;
    resolve?: Function;
}

const cache: Record<string, CacheEntry> = {}
const debounceMillis = 250

async function fetchAll(doc: vscode.TextDocument): Promise<Object> {
    const docVersion = doc.version
    const docUri = doc.uri.toString()

    // 1) If another callback is already fetching for this doc version (or newer), wait for that result:
    let entry = cache[docUri]
    if (entry && entry.version >= docVersion) {
        return entry.promise
    }

    // 2) Otherwise, create a promise to fetch so other callbacks for this doc version can wait for you:
    entry = { version: docVersion }
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    entry.promise = new Promise((resolve, _reject) => {
        entry.resolve = resolve
    })
    cache[docUri] = entry

    // 3) Debounce: wait a bit, if newer version of doc is already being processed, use those results instead:
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    await new Promise((resolve, _reject) => setTimeout(resolve, debounceMillis))

    const newerEntry = cache[docUri]
    if (newerEntry && newerEntry.version > docVersion) {
        // 4) If a fetch is pending for an even newer doc version in the meantime, wait for that, but also forward
        // the result to your sibling callbacks that are waiting for your promise from 2):
        const data = await newerEntry.promise
        entry.resolve(data)
        return data
    }
    else {
        // 5) If no one has fetched it yet, finally fetch it yourself:
        const data = await doFetchAll(doc)
        entry.resolve(data)
        return data
    }
}

async function doFetchAll(doc: vscode.TextDocument) {
    const todos = parseMomentsString(doc.getText(), createParseConfig())
    const formatType = doc.languageId === trashLangId ? TRASH_FORMAT : TODO_FORMAT
    return {
        todos,
        format: formatTodos(todos, doc.getText(), formatType),
        fold: foldTodos(todos),
        outline: outlineTodos(todos, doc.getText(), formatType),
        preview: previewMoments(todos)
    }
}

function getter<T>(key: string): (document: vscode.TextDocument) => Promise<T> {
    return async (document: vscode.TextDocument) => {
        const docVersion = document.version
        const res = await fetchAll(document)
        if (document.version > docVersion) {
            // Don't use result if a new doc version was created already, otherwise we run into
            // race conditions where it may use the result of an older doc version.
            return Promise.reject(new Error('Newer doc version'))
        }
        return Promise.resolve(res[key])
    }
}

export const requestFormat = getter<FormatStyle[]>('format')
export const requestFold = getter<number[][]>('fold')
export const requestOutline = getter<Outline[]>('outline')
export const requestPreview = getter('preview')
export const requestTodos = getter<Todos>('todos')

export async function cleanTodos(document: vscode.TextDocument): Promise<void> {
    await doBackup(document.uri.fsPath)

    const workspaceEdit = toTodoWorkspaceEdit(cleanDoneMoments(document.getText()), document)
    await vscode.workspace.applyEdit(workspaceEdit)
    await document.save()
}

export async function trashTodos(document: vscode.TextDocument): Promise<void> {
    const trashFileUri = vscode.Uri.parse(document.uri.toString().replace(/\.([^.]+)$/, '-trash.$1'))

    await Promise.all([
        doBackup(document.uri.fsPath),
        doBackup(trashFileUri.fsPath)
    ])

    const [todoEdits, trashEdits] = trashDoneMoments(document.getText())
    const todoWorkspaceEdit = toTodoWorkspaceEdit(todoEdits, document)
    const trashWorkspaceEdit = toTrashWorkspaceEdits(trashEdits, trashFileUri)

    await Promise.all([
        vscode.workspace.applyEdit(trashWorkspaceEdit),
        vscode.workspace.applyEdit(todoWorkspaceEdit)
    ])

    const trashDoc = vscode.workspace.textDocuments.find(doc => doc.uri.toString() === trashFileUri.toString())
    await Promise.all([
        trashDoc.save(),
        document.save()
    ])
}

function toTodoWorkspaceEdit(edits: Edit[], document: vscode.TextDocument): vscode.WorkspaceEdit {
    const workspaceEdit = new vscode.WorkspaceEdit()

    edits.forEach(edit => {
        if (edit.type === EditType.INSERT) {
            const insertEdit = edit as InsertEdit
            const pos = insertEdit.offset === EOF_OFFSET ? document.lineAt(document.lineCount - 1).range.end : document.positionAt(insertEdit.offset)
            workspaceEdit.insert(document.uri, pos, insertEdit.content)
        }
        else if (edit.type === EditType.DELETE) {
            const deleteEdit = edit as DeleteEdit
            workspaceEdit.delete(document.uri, new vscode.Range(document.positionAt(deleteEdit.startOffset), document.positionAt(deleteEdit.endOffset)))
        }
    })
    return workspaceEdit
}

function toTrashWorkspaceEdits(edits: Edit[], uri: vscode.Uri): vscode.WorkspaceEdit {
    const workspaceEdit = new vscode.WorkspaceEdit()
    workspaceEdit.createFile(uri, { ignoreIfExists: true })

    edits.forEach(edit => {
        if (edit.type !== EditType.INSERT) {
            throw Error('Can only apply insert edits in trash file')
        }
        const insertEdit = edit as InsertEdit
        if (insertEdit.offset !== EOF_OFFSET) {
            throw Error('Can only insert edits with EOF_OFFSET in trash file')
        }
        workspaceEdit.insert(uri, new vscode.Position(Number.MAX_VALUE, Number.MAX_VALUE), insertEdit.content)
    })

    return workspaceEdit
}

async function doBackup(file: string) {
    try {
        await fs.promises.stat(file)
    }
    catch (err) {
        if (err.code === 'ENOENT') {
            return
        }
        throw err
    }

    const backupDir = path.join(path.dirname(file), 'backup')
    return backup(file, backupDir)
}
