import * as vscode from 'vscode'
import { requestTodos } from './lib'
import { todoOrTrashSelector } from './util'
import { getBottomLine } from '@commonplace/lib'

interface Item extends vscode.QuickPickItem {
    range: vscode.Range
}

export async function showSearchPick() {
    const doc = vscode.window.activeTextEditor?.document
    if (!doc || vscode.languages.match(todoOrTrashSelector, doc) <= 0) {
        return
    }

    const todos = await requestTodos(doc)
    const quickPickEntries: Item[] = todos.moments.map(m => {
        const start = m.docPos.lineNum
        const end = getBottomLine(m)
        const range = new vscode.Range(doc.lineAt(start).range.start, doc.lineAt(end).range.end)
        const detail = end > start ? doc.getText(range.with(doc.lineAt(start + 1).range.start)) : ''
        return {
            label: m.name,
            detail,
            description: m.category?.name,
            range
        }
    })

    // Note: the quick pick unfortunately does not use VSCode's more powerful fuzzy search yet:
    // https://github.com/microsoft/vscode/issues/34088
    const pick = vscode.window.createQuickPick<Item>()
    pick.items = quickPickEntries
    pick.canSelectMany = false
    pick.matchOnDescription = false
    pick.matchOnDetail = true

    pick.onDidChangeActive(items => {
        if (!items.length) return

        vscode.window.activeTextEditor.revealRange(
            items[0].range, vscode.TextEditorRevealType.InCenter)
        vscode.window.activeTextEditor.selection = new vscode.Selection(items[0].range.start, items[0].range.end)
    })

    pick.onDidAccept(() => pick.hide())

    pick.show()
}
