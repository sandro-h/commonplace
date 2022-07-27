import * as vscode from 'vscode'

export const todoLangId = 'todo'
export const trashLangId = 'todo-trash'
export const todoSelector: vscode.DocumentSelector = { language: todoLangId }
export const trashSelector: vscode.DocumentSelector = { language: trashLangId }
export const todoOrTrashSelector: vscode.DocumentSelector = [todoSelector, trashSelector]
