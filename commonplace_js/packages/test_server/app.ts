import { parseMomentsString, inLocalTimezone } from "@commonplace/lib";
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
        return inLocalTimezone(this?.[k]).toISOString().replace(/Z$/, '');
    }
    return v;
}

app.post('/parse', (req, res) => {
    const body = Buffer.from(req.body, 'base64').toString('utf8');
    console.log('query', req.query);

    try {
        const cfg = createParseConfig();
        if (req.query.fixedTime || req.query.fixed_time) {
            cfg.fixedTime = parse((req.query.fixedTime ?? req.query.fixed_time) as string, 'yyyy-MM-dd', new Date())
        }

        const todos = parseMomentsString(body, cfg);
        console.log(typeof (todos.moments[0] as SingleMoment).end?.dt.getMonth === 'function')

        res.send(JSON.stringify(todos, req.query.localTime ? useLocalTimezoneDates : undefined));
    }
    catch (e) {
        console.error('could not parse', e);
        res.json({});
    }


})


app.listen(port, () => {
    console.log(`Example app listening on port ${port}`)
})