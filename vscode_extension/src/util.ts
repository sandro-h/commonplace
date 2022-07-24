import * as vscode from 'vscode'

// via https://davidwalsh.name/javascript-debounce-function
export function debounce(func: Function, wait: number, immediate?: boolean): Function {
  let timeout
  return function () {
    const context = this
    const args = arguments
    const later = function () {
      timeout = null
      if (!immediate) func.apply(context, args)
    }
    const callNow = immediate && !timeout
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
    if (callNow) func.apply(context, args)
  }
}

export const todoLangId = 'todo'
export const trashLangId = 'todo-trash'
export const todoSelector: vscode.DocumentSelector = { language: todoLangId }
export const trashSelector: vscode.DocumentSelector = { language: trashLangId }
export const todoOrTrashSelector: vscode.DocumentSelector = [todoSelector, trashSelector]
