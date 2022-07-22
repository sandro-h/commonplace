import * as vscode from 'vscode';
import * as formatting from './formatting';
import * as folding from './folding';
import * as outline from './outline';
import * as commands from './commands';
import * as preview from './preview';
import * as links from './links';
import { VSCodeCommonplaceConfig } from './config';

// this method is called when vs code is activated
export function activate(context: vscode.ExtensionContext) {
	formatting.activate(context);
	folding.activate();
	outline.activate();
	commands.activate(context);
	preview.activate(context);
	links.activate(VSCodeCommonplaceConfig);
}
