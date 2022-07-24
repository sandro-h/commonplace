import * as vscode from 'vscode'
import { requestFold } from './lib'
import { todoOrTrashSelector } from './util'

export function activate() {
  vscode.languages.registerFoldingRangeProvider(
    todoOrTrashSelector,
    new CommonplaceFoldingRangeProvider()
  )
}

class CommonplaceFoldingRangeProvider implements vscode.FoldingRangeProvider {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  async provideFoldingRanges(document: vscode.TextDocument, context: vscode.FoldingContext, token: vscode.CancellationToken): Promise<vscode.FoldingRange[]> {
    try {
      const foldLines = await requestFold(document)
      return foldLines.map(fold => new vscode.FoldingRange(fold[0], fold[1], vscode.FoldingRangeKind.Region))
    }
    catch {
      return null
    }
  }
}
