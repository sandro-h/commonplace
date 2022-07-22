import * as vscode from 'vscode';
import { requestOutline } from './lib';
import { todoOrTrashSelector } from './util';

export function activate() {
	vscode.languages.registerDocumentSymbolProvider(
		todoOrTrashSelector,
		new CommonplaceSymbolProvider()
	);
}

class CommonplaceSymbolProvider implements vscode.DocumentSymbolProvider {

	async provideDocumentSymbols(document: vscode.TextDocument, token: vscode.CancellationToken): Promise<vscode.DocumentSymbol[]> {
		const outline = await requestOutline(document);
		return outline.map(o => new vscode.DocumentSymbol(
			o.name, o.detail,
			vscode.SymbolKind.Event,
			new vscode.Range(o.startLine, 0, o.endLine, 1000),
			new vscode.Range(o.startLine, 0, o.endLine, 1000),
		));
	}
}
