import * as vscode from 'vscode'
import { CommonplaceConfig } from './config'
import { todoOrTrashSelector } from './util'

interface CommonplaceLinkDefinition {
    pattern: string;
    url: string;
}

export function activate(cfg: CommonplaceConfig) {
    vscode.languages.registerDocumentLinkProvider(
        todoOrTrashSelector,
        new CommonplaceDocumentLinkProvider(cfg)
    )
}

class CommonplaceDocumentLinkProvider implements vscode.DocumentLinkProvider {
    cfg: CommonplaceConfig

    constructor(cfg: CommonplaceConfig) {
        this.cfg = cfg
    }

    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    provideDocumentLinks(document: vscode.TextDocument, _token: vscode.CancellationToken): vscode.DocumentLink[] {
        const linkDefs = this.getLinkDefs()
        if (!linkDefs.length) {
            return
        }

        const text = document.getText()
        return linkDefs.flatMap(def => this.extractLinksForDef(def, text, document))
    }

    getLinkDefs(): CommonplaceLinkDefinition[] {
        if (!this.cfg.getTicketPattern() || !this.cfg.getTicketUrl()) {
            return []
        }

        return [
            {
                pattern: this.cfg.getTicketPattern(),
                url: this.cfg.getTicketUrl()
            }
        ]
    }

    extractLinksForDef(def: CommonplaceLinkDefinition, text: string, document: vscode.TextDocument): vscode.DocumentLink[] {
        const re = new RegExp(def.pattern, 'g')
        const links = []
        let match: RegExpExecArray
        while ((match = re.exec(text)) !== null) {
            const uri = vscode.Uri.parse(def.url.replace('$1', text.slice(match.index, match.index + match[0].length)))
            const pos = document.positionAt(match.index)
            const link = new vscode.DocumentLink(new vscode.Range(pos, pos.translate(0, match[0].length)), uri)
            links.push(link)
        }

        return links
    }
}
