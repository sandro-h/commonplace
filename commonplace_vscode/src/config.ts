import * as vscode from 'vscode';

export interface CommonplaceConfig {
	getRestUrl(): string;
	getTodoFileName(): string;
	getTicketPattern(): string;
	getTicketUrl(): string;
}

export const VSCodeCommonplaceConfig: CommonplaceConfig = {
	getRestUrl: configGetter('restUrl'),
	getTodoFileName: configGetter('todoFileName'),
	getTicketPattern: configGetter('ticketPattern'),
	getTicketUrl: configGetter('ticketUrl'),
};

function configGetter<T>(key: string): () => T {
	return () => vscode.workspace.getConfiguration('commonplace').get<T>(key);
}
