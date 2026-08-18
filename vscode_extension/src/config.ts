import * as vscode from 'vscode'

export interface CommonplaceConfig {
    getTicketPattern(): string | undefined;
    getTicketUrl(): string | undefined;
}

export const VSCodeCommonplaceConfig: CommonplaceConfig = {
    getTicketPattern: () => getConfig('ticketPattern'),
    getTicketUrl: () => getConfig('ticketUrl')
}

function getConfig<T>(key: string): T | undefined {
    return vscode.workspace.getConfiguration('commonplace').get<T>(key)
}
