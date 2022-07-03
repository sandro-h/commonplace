import * as vscode from 'vscode';
import { outlineTodos } from './client';
import { CommonplaceConfig } from './config';
import { todoOrTrashSelector } from './util';

export function activate(cfg: CommonplaceConfig) {
	vscode.languages.registerDocumentSymbolProvider(
		todoOrTrashSelector,
		new CommonplaceSymbolProvider(cfg.getRestUrl())
	);
}

class CommonplaceSymbolProvider implements vscode.DocumentSymbolProvider {

	restUrl: string;

	constructor(restUrl: string) {
		this.restUrl = restUrl
	}

	async provideDocumentSymbols(document: vscode.TextDocument, token: vscode.CancellationToken): Promise<vscode.DocumentSymbol[]> {
		const outline = await outlineTodos(document, this.restUrl);
		return outline.map(o => new vscode.DocumentSymbol(
			o["name"], o["detail"],
			vscode.SymbolKind.Event,
			new vscode.Range(o["line"], 0, o["line"], 0),
			new vscode.Range(o["line"], 0, o["line"], 0)
		));
	}
}
