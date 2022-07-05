import * as vscode from 'vscode';
import * as formatting from './formatting';
import * as folding from './folding';
import * as outline from './outline';
import * as commands from './commands';
import * as preview from './preview';
import * as links from './links';
import { VSCodeCommonplaceConfig } from './config';
import { foo, bar } from '@commonplace/lib';

// this method is called when vs code is activated
export function activate(context: vscode.ExtensionContext) {
	formatting.activate(context, VSCodeCommonplaceConfig);
	folding.activate(VSCodeCommonplaceConfig);
	outline.activate(VSCodeCommonplaceConfig);
	commands.activate(context, VSCodeCommonplaceConfig);
	preview.activate(context, VSCodeCommonplaceConfig);
	links.activate(VSCodeCommonplaceConfig);
	let orange = vscode.window.createOutputChannel("Orange");
	orange.appendLine(foo());
	orange.appendLine(bar());
}
