import * as vscode from 'vscode'
import { cleanTodos, trashTodos } from './lib'

const INDENT_PATTERN = /(^|\r?\n)(\s+)/
const log = vscode.window.createOutputChannel('commonplace.commands')

async function handleClean() {
    try {
        await cleanTodos(vscode.window.activeTextEditor.document)
        vscode.window.showInformationMessage('Cleaned done todos!')
    }
    catch (err) {
        log.appendLine(err)
        log.appendLine(err.stack)
        vscode.window.showErrorMessage(`Failed to clean done todos: ${err}`)
    }
}

async function handleTrash() {
    try {
        await trashTodos(vscode.window.activeTextEditor.document)
        vscode.window.showInformationMessage('Trashed done todos!')
    }
    catch (err) {
        vscode.window.showErrorMessage(`Failed to trash done todos: ${err}`)
    }
}

async function handleCopyWithoutIndent() {
    try {
        const editor = vscode.window.activeTextEditor
        if (!editor || !editor.selections) {
            return
        }

        let selectedText = editor.document.getText(editor.selections[0])
        const m = selectedText.match(INDENT_PATTERN)
        if (m) {
            const indent = new RegExp('(^|\r?\n)' + m[2], 'g')
            selectedText = selectedText.replace(indent, '$1')
        }

        vscode.env.clipboard.writeText(selectedText)
    }
    catch (err) {
        vscode.window.showErrorMessage(`Failed to copy without indentation: ${err}`)
    }
}

export function activate(context: vscode.ExtensionContext) {
    context.subscriptions.push(vscode.commands.registerCommand('commonplace.clean', handleClean))
    context.subscriptions.push(vscode.commands.registerCommand('commonplace.trash', handleTrash))
    context.subscriptions.push(vscode.commands.registerCommand('commonplace.copy', handleCopyWithoutIndent))
}
