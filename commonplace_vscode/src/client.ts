import fetch from 'node-fetch';
import * as vscode from 'vscode';
import { trashLangId } from './util';

interface CacheEntry {
    version: number;
    promise?: Promise<Object>;
    resolve?: Function;
}

const cache: Record<string, CacheEntry> = {};
const debounceMillis = 250;
const log = vscode.window.createOutputChannel("commonplace.client");

async function fetchAll(doc: vscode.TextDocument, restUrl: string): Promise<Object> {
    const docVersion = doc.version;
    const docUri = doc.uri.toString();

    // 1) If another callback is already fetching for this doc version (or newer), wait for that result:
    let entry = cache[docUri];
    if (entry && entry.version >= docVersion) {
        return entry.promise;
    }

    // 2) Otherwise, create a promise to fetch so other callbacks for this doc version can wait for you:
    entry = { version: docVersion }
    entry.promise = new Promise((resolve, _) => {
        entry.resolve = resolve;
    })
    cache[docUri] = entry;

    // 3) Debounce: wait a bit, if newer version of doc is already being processed, use those results instead:
    await new Promise(r => setTimeout(r, debounceMillis));

    const newerEntry = cache[docUri];
    if (newerEntry && newerEntry.version > docVersion) {
        // 4) If a fetch is pending for an even newer doc version in the meantime, wait for that, but also forward
        // the result to your sibling callbacks that are waiting for your promise from 2):
        const data = await newerEntry.promise;
        entry.resolve(data);
        return data;
    }
    else {
        // 5) If no one has fetched it yet, finally fetch it yourself:
        const data = await doFetchAll(doc, restUrl);
        entry.resolve(data);
        return data;
    }
}

async function doFetchAll(doc: vscode.TextDocument, restUrl: string) {
    log.appendLine("calling rest");
    const res = await fetch(
        `${restUrl}/all?type=${doc.languageId == trashLangId ? 'trash' : 'todo'}`,
        {
            method: 'POST',
            headers: { 'content-type': 'text/plain' },
            body: Buffer.from(doc.getText()).toString('base64')
        });

    return res.json();
}

export async function formatTodos(document: vscode.TextDocument, restUrl: string): Promise<string[]> {
    const res = await fetchAll(document, restUrl);
    return res["format"].split(/\r?\n/);
}

export async function foldTodos(document: vscode.TextDocument, restUrl: string): Promise<string[]> {
    const res = await fetchAll(document, restUrl);
    return res["fold"].split(/\r?\n/);
}

export async function outlineTodos(document: vscode.TextDocument, restUrl: string): Promise<Object[]> {
    const res = await fetchAll(document, restUrl);
    return res["outline"];
}

export async function preview(document: vscode.TextDocument, restUrl: string): Promise<string[]> {
    const res = await fetchAll(document, restUrl);
    return res["preview"];
}

export async function cleanTodos(restUrl: string): Promise<void> {
    await fetch(`${restUrl}/clean`, { method: 'POST' });
}

export async function trashTodos(restUrl: string): Promise<void> {
    await fetch(`${restUrl}/trash`, { method: 'POST' });
}
