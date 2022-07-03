import * as vscode from 'vscode';
import { CommonplaceConfig } from './config';
import { foldTodos } from './client';
import { todoOrTrashSelector, trashLangId } from './util';

export function activate(cfg: CommonplaceConfig) {
	vscode.languages.registerFoldingRangeProvider(
		todoOrTrashSelector,
		new CommonplaceFoldingRangeProvider(cfg.getRestUrl())
	);
}

class CommonplaceFoldingRangeProvider implements vscode.FoldingRangeProvider {

	restUrl: string;

	constructor(restUrl: string) {
		this.restUrl = restUrl
	}

	async provideFoldingRanges(document: vscode.TextDocument, context: vscode.FoldingContext, token: vscode.CancellationToken): Promise<vscode.FoldingRange[]> {
		const foldLines = await foldTodos(document, this.restUrl);
		return foldLines.map(line => {
			let parts = line.split('-');
			return new vscode.FoldingRange(
				parseInt(parts[0]),
				parseInt(parts[1]),
				vscode.FoldingRangeKind.Region
			);
		});
	}
}