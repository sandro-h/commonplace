import * as vscode from 'vscode';
import { CommonplaceConfig } from './config';
import { cleanTodos, trashTodos } from './client';

const INDENT_PATTERN = /(^|\r?\n)(\s+)/;

async function handleClean(cfg: CommonplaceConfig) {
	try {
		await cleanTodos(cfg.getRestUrl());
		vscode.window.showInformationMessage('Cleaned done todos!');
	}
	catch (err) {
		vscode.window.showErrorMessage(`Failed to clean done todos: ${err}`);
	}
}

async function handleTrash(cfg: CommonplaceConfig) {
	try {
		await trashTodos(cfg.getRestUrl());
		vscode.window.showInformationMessage('Trashed done todos!');
	}
	catch (err) {
		vscode.window.showErrorMessage(`Failed to trash done todos: ${err}`);
	}
}

async function handleCopyWithoutIndent() {
	try {
		const editor = vscode.window.activeTextEditor;
		if (!editor || !editor.selections) {
			return;
		}

		let selectedText = editor.document.getText(editor.selections[0]);
		const m = selectedText.match(INDENT_PATTERN);
		if (m) {
			const indent = new RegExp('(^|\r?\n)' + m[2], 'g');
			selectedText = selectedText.replace(indent, "$1");
		}

		vscode.env.clipboard.writeText(selectedText);
	}
	catch (err) {
		vscode.window.showErrorMessage(`Failed to copy without indentation: ${err}`);
	}
}

export function activate(context: vscode.ExtensionContext, cfg: CommonplaceConfig) {
	context.subscriptions.push(vscode.commands.registerCommand('commonplace.clean', () => handleClean(cfg)));
	context.subscriptions.push(vscode.commands.registerCommand('commonplace.trash', () => handleTrash(cfg)));
	context.subscriptions.push(vscode.commands.registerCommand('commonplace.copy', handleCopyWithoutIndent));
}
