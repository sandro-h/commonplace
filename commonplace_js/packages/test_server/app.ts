import {
    parseMomentsString, inLocalTimezone, generateInstances, isoTimezoneOffset, formatTodos, createParseConfig,
    TODO_FORMAT, foldTodos, outlineTodos, cleanDoneMoments, trashDoneMoments, EditType, InsertEdit, DeleteEdit, Edit, EOF_OFFSET
} from "@commonplace/lib";
import express from "express";
import { format, parse } from "date-fns"
import * as fs from 'fs';
import * as path from 'path';

const app = express()
app.use(express.text({ type: "*/*" }))
const port = 3000

app.get('/', (req, res) => {
    res.send('Hello World!')
})

function useLocalTimezoneDates(this: any, k: any, v: any) {
    if (this?.[k] instanceof Date) {
        if (k === 'timeOfDay') {
            return format(this?.[k], 'HH:mm:ss');
        }
        else {
            return inLocalTimezone(this?.[k]).toISOString().replace(/Z$/, isoTimezoneOffset(this?.[k]));
        }
    }
    return v;
}

app.post('/parse', (req, res) => {
    const body = Buffer.from(req.body, 'base64').toString('utf8');

    try {
        const cfg = createParseConfig();
        if (req.query.fixedTime || req.query.fixed_time) {
            cfg.fixedTime = parse((req.query.fixedTime ?? req.query.fixed_time) as string, 'yyyy-MM-dd', new Date())
        }

        const todos = parseMomentsString(body, cfg);

        res.send(JSON.stringify(todos, req.query.localTime ? useLocalTimezoneDates : undefined));
    }
    catch (e) {
        console.error('could not parse', e);
        res.json({});
    }
})

app.post('/instances', (req, res) => {
    const body = Buffer.from(req.body, 'base64').toString('utf8');

    try {
        const cfg = createParseConfig();
        if (req.query.fixedTime || req.query.fixed_time) {
            cfg.fixedTime = parse((req.query.fixedTime ?? req.query.fixed_time) as string, 'yyyy-MM-dd', new Date())
        }

        const todos = parseMomentsString(body, cfg);

        const start = parse(req.query.start as string, 'yyyy-MM-dd', new Date())
        const end = parse(req.query.end as string, 'yyyy-MM-dd', new Date())
        const instances = generateInstances(todos.moments, start, end)

        res.send(JSON.stringify(instances, req.query.localTime ? useLocalTimezoneDates : undefined));
    }
    catch (e) {
        console.error('could not instantiate', e);
        res.json({});
    }
})

app.post('/format', (req, res) => {
    const body = Buffer.from(req.body, 'base64').toString('utf8');

    try {
        const cfg = createParseConfig();
        if (req.query.fixedTime || req.query.fixed_time) {
            cfg.fixedTime = parse((req.query.fixedTime ?? req.query.fixed_time) as string, 'yyyy-MM-dd', new Date())
        }

        const todos = parseMomentsString(body, cfg);

        const formatType = req.query.type as string ?? TODO_FORMAT
        const styles = formatTodos(todos, body, formatType, cfg.fixedTime)
        res.send(styles.reduce((p, c) => `${p}${c.start},${c.end},${c.style}\n`, ''));
    }
    catch (e) {
        console.error('could not instantiate', e);
        res.json({});
    }
})

app.post('/folding', (req, res) => {
    const body = Buffer.from(req.body, 'base64').toString('utf8');

    try {
        const cfg = createParseConfig();
        if (req.query.fixedTime || req.query.fixed_time) {
            cfg.fixedTime = parse((req.query.fixedTime ?? req.query.fixed_time) as string, 'yyyy-MM-dd', new Date())
        }

        const todos = parseMomentsString(body, cfg);

        const folds = foldTodos(todos)
        res.send(folds.reduce((p, [start, end]) => `${p}${start}-${end}\n`, ''));
    }
    catch (e) {
        console.error('could not instantiate', e);
        res.json({});
    }
})

app.post('/outline', (req, res) => {
    const body = Buffer.from(req.body, 'base64').toString('utf8');

    try {
        const cfg = createParseConfig();
        if (req.query.fixedTime || req.query.fixed_time) {
            cfg.fixedTime = parse((req.query.fixedTime ?? req.query.fixed_time) as string, 'yyyy-MM-dd', new Date())
        }

        const todos = parseMomentsString(body, cfg);

        const formatType = req.query.type as string ?? TODO_FORMAT
        const outline = outlineTodos(todos, body, formatType)
        res.json({ outline })
    }
    catch (e) {
        console.error('could not instantiate', e);
        res.json({});
    }
})

app.post('/clean', (req, res) => {
    try {
        const testTodoDir = path.join("c:/temp", 'commonplace_system_test')
        const todoFile = path.join(testTodoDir, "todo.txt");
        const content = fs.readFileSync(todoFile).toString()
        const edits = cleanDoneMoments(content)
        const updated = applyEdits(content, edits);
        fs.writeFileSync(todoFile, updated);
        res.sendStatus(200);
    }
    catch (e) {
        console.error('could not instantiate', e);
        res.json({});
    }
})

app.post('/trash', (req, res) => {
    try {
        const cfg = createParseConfig();
        if (req.query.fixedTime || req.query.fixed_time) {
            cfg.fixedTime = parse((req.query.fixedTime ?? req.query.fixed_time) as string, 'yyyy-MM-dd', new Date())
        }

        const testTodoDir = path.join("c:/temp", 'commonplace_system_test')
        const todoFile = path.join(testTodoDir, "todo.txt");
        const trashFile = path.join(testTodoDir, "todo-trash.txt");
        const content = fs.readFileSync(todoFile).toString()
        const [todoEdits, trashEdits] = trashDoneMoments(content, cfg, cfg.fixedTime)

        const updatedTodo = applyEdits(content, todoEdits);
        const updatedTrash = applyEdits("", trashEdits);

        fs.writeFileSync(todoFile, updatedTodo);
        fs.writeFileSync(trashFile, updatedTrash);

        res.sendStatus(200);
    }
    catch (e) {
        console.error('could not instantiate', e);
        res.json({});
    }
})

function applyEdits(content: string, edits: Edit[]): string {
    const inserts = edits.filter(e => e.type === EditType.INSERT);
    const deletes = edits.filter(e => e.type === EditType.DELETE);

    let updated = content;
    (deletes as DeleteEdit[]).forEach(del => {
        updated = updated.slice(0, del.startOffset) + "~".repeat(del.endOffset - del.startOffset) + updated.slice(del.endOffset)
    });

    (inserts as InsertEdit[]).forEach(i => i.offset = i.offset === EOF_OFFSET ? content.length : i.offset)

    for (let i = 0; i < inserts.length; i++) {
        const insert = inserts[i] as InsertEdit;
        updated = updated.slice(0, insert.offset) + insert.content + updated.slice(insert.offset)
        for (let j = i + 1; j < inserts.length; j++) {
            const nextInsert = inserts[j] as InsertEdit;
            if (nextInsert.offset >= insert.offset) {
                nextInsert.offset += insert.content.length;
            }
        }
    }

    return updated.replace(/~/g, "");
}

function fileReader(file: string) {
    return () => fs.readFileSync(file).toString();
}

function fileWriter(file: string) {
    return (content: string) => fs.writeFileSync(file, content);
}

function fileAppender(file: string) {
    return (content: string) => fs.appendFileSync(file, content);
}

app.listen(port, () => {
    console.log(`Example app listening on port ${port}`)
})