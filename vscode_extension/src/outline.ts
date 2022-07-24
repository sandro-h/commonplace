import * as vscode from 'vscode'
import { requestOutline } from './lib'
import { todoOrTrashSelector } from './util'

export function activate() {
    vscode.languages.registerDocumentSymbolProvider(
        todoOrTrashSelector,
        new CommonplaceSymbolProvider()
    )
}

class CommonplaceSymbolProvider implements vscode.DocumentSymbolProvider {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    async provideDocumentSymbols(document: vscode.TextDocument, _token: vscode.CancellationToken): Promise<vscode.DocumentSymbol[]> {
        try {
            const outline = await requestOutline(document)
            return outline.map(o => new vscode.DocumentSymbol(
                o.name, o.detail,
                vscode.SymbolKind.Event,
                new vscode.Range(o.startLine, 0, o.endLine, 1000),
                new vscode.Range(o.startLine, 0, o.endLine, 1000)
            ))
        }
        catch {
            return null
        }
    }
}
