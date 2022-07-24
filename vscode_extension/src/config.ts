import * as vscode from 'vscode'

export interface CommonplaceConfig {
  getTicketPattern(): string;
  getTicketUrl(): string;
}

export const VSCodeCommonplaceConfig: CommonplaceConfig = {
  getTicketPattern: () => getConfig('ticketPattern'),
  getTicketUrl: () => getConfig('ticketUrl')
}

function getConfig<T>(key: string): T {
  return vscode.workspace.getConfiguration('commonplace').get<T>(key)
}
