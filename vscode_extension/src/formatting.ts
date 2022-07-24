import * as vscode from 'vscode'
import { todoOrTrashSelector } from './util'
import { FormatStyle } from '@commonplace/lib'
import { requestFormat } from './lib'

type FormatDefinition = {
    dec: vscode.TextEditorDecorationType;
    hoverMessage?: string;
}

type Format = FormatDefinition & { list: vscode.DecorationOptions[] };

function initFormats(context: vscode.ExtensionContext): Record<string, FormatDefinition> {
    const fmts: Record<string, FormatDefinition> = {
        cat: {
            dec: vscode.window.createTextEditorDecorationType({
                color: 'orange; font-weight: bold'
            })
        },
        mom: {
            dec: vscode.window.createTextEditorDecorationType({
                color: 'inherit; font-weight: bold'
            })
        },
        'mom.priority': {
            dec: vscode.window.createTextEditorDecorationType({
                color: 'inherit; font-weight: bold',
                border: 'solid 1px red'
            })
        },
        'mom.done': {
            dec: vscode.window.createTextEditorDecorationType({
                color: '#1e420f; font-weight: bold'
            })
        },
        date: {
            dec: vscode.window.createTextEditorDecorationType({
                after: {
                    contentIconPath: context.asAbsolutePath('cal.png')
                }
            }),
            hoverMessage: 'Date'
        },
        time: {
            dec: vscode.window.createTextEditorDecorationType({
                after: {
                    contentIconPath: context.asAbsolutePath('time.png')
                }
            }),
            hoverMessage: 'Time'
        },
        id: {
            dec: vscode.window.createTextEditorDecorationType({
                color: '#3f679a'
            }),
            hoverMessage: 'ID'
        },
        'com.done': {
            dec: vscode.window.createTextEditorDecorationType({
                color: '#1e420f;'
            })
        }
    }

    const dueStyles = [
        { textDecoration: 'none; font-weight: bold', color: '#ff0000' },
        { textDecoration: 'none; font-weight: bold', color: '#ff4040' },
        { textDecoration: 'none; font-weight: bold', color: '#ff7d7d' },
        { textDecoration: 'none; font-weight: bold', color: '#fea4a4' },
        { textDecoration: 'none; font-weight: bold', color: '#fec7c7' }
    ]

    const momUntilDecorationTypes = {}
    for (let i = 0; i <= 11; i += 1) {
        let styleIndex = -1
        if (i <= 1) styleIndex = 0
        else if (i <= 2) styleIndex = 1
        else if (i <= 4) styleIndex = 2
        else if (i <= 7) styleIndex = 3
        else if (i <= 11) styleIndex = 4

        if (styleIndex > -1) {
            momUntilDecorationTypes[`mom.until${i}`] = vscode.window.createTextEditorDecorationType(dueStyles[styleIndex])
            momUntilDecorationTypes[`mom.until${i}.priority`] = vscode.window.createTextEditorDecorationType({
                ...dueStyles[styleIndex],
                border: 'solid 1px red'
            })
        }
    }

    for (const key in momUntilDecorationTypes) {
        fmts[key] = { dec: momUntilDecorationTypes[key] }
    }

    return fmts
}

function applyFormatting(styles: FormatStyle[], formats: Record<string, FormatDefinition>, document: vscode.TextDocument): Record<string, Format> {
    const res: Record<string, Format> = {}
    for (const key in formats) {
        res[key] = {
            ...formats[key],
            list: []
        }
    }

    styles.forEach(style => {
        const fmt = res[style.style]

        if (fmt) {
            fmt.list.push({
                range: new vscode.Range(document.positionAt(style.start), document.positionAt(style.end)),
                hoverMessage: fmt.hoverMessage
            })
        }
    })

    return res
}

export function activate(context: vscode.ExtensionContext) {
    const formats = initFormats(context)
    let activeEditor: vscode.TextEditor | null = null

    setActiveEditor(vscode.window.activeTextEditor)
    updateDecorations()

    vscode.window.onDidChangeActiveTextEditor(editor => {
        setActiveEditor(editor)
        updateDecorations()
    }, null, context.subscriptions)

    vscode.workspace.onDidChangeTextDocument(event => {
        if (activeEditor && event.document === activeEditor.document) {
            updateDecorations()
        }
    }, null, context.subscriptions)

    function setActiveEditor(editor: vscode.TextEditor) {
        activeEditor = isTodoEditor(editor) ? editor : null
    }

    function isTodoEditor(editor: vscode.TextEditor) {
        if (!editor || !editor.document) return false
        return vscode.languages.match(todoOrTrashSelector, editor.document) > 0
    }

    async function updateDecorations() {
        if (!activeEditor) return

        // Using then syntax here because we ignore the reject case which happens if a newer doc version
        // was created in the meantime.
        requestFormat(activeEditor.document)
            .then(styles => {
                const fmts = applyFormatting(styles, formats, activeEditor.document)
                for (const key in fmts) {
                    const fmt = fmts[key]
                    // Note: it's important to also set if the list is empty, to disable old decorations on the line.
                    activeEditor.setDecorations(fmt.dec, fmt.list)
                }
            })
            .catch(() => { })
    }
}
