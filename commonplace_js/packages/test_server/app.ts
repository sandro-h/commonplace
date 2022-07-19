import { parseMomentsString, inLocalTimezone, generateInstances, isoTimezoneOffset } from "@commonplace/lib";
import { createParseConfig, SingleMoment } from "@commonplace/lib/dist/models";
import express from "express";
import { format, parse } from "date-fns"

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

app.listen(port, () => {
    console.log(`Example app listening on port ${port}`)
})