const puppeteer = require("puppeteer")
const fs = require('fs')

const cal = fs.readFileSync(`${__dirname}/../../vscode_extension/cal.png`).toString('base64')
const calImg = `<img src="data:image/png;base64,${cal}">`
const time = fs.readFileSync(`${__dirname}/../../vscode_extension/time.png`).toString('base64')
const timeImg = `<img src="data:image/png;base64,${time}">`

const samples = [
    'category',
    `------------------
     <span style="color:orange">My category</span>
    ------------------`,

    'colored_category',
    `------------------
     <span style="color:orange">My category [Coral]</span>
    ------------------`,

    'todo',
    `<strong>[] my open todo</strong>
    <span style="color:darkgreen">[x] my done todo</span>`,

    'hierarchical',
    `<strong>[] my top-level todo</strong>
        <strong>[] my child todo</strong>
        <span style="color:darkgreen">[x] my done child todo
            [] more stuff</span>`,

    'workstates',
    `<strong>[] my open todo</strong>
    <strong>[p] my in progress todo</strong>
    <strong>[w] my waiting todo</strong>
    <span style="color:darkgreen">[x] my done todo</span>`,

    'comments',
    `<strong>[] my top-level todo</strong>
        some random comment.
        it needs to be indented.

        <strong>[] child todo</strong>
            a comment for the child todo`,

    'specific_day',
    `<strong>[] get groceries (15.11.20${calImg})</strong>`,

    'specific_day_time',
    `<strong>[] get groceries (15.11.20${calImg} 08:00${timeImg})</strong>`,

    'time range',
    `<strong>[] vacation (10.11.20-15.11.20${calImg})</strong>
    <strong>[] new house (10.11.20-${calImg})</strong>
    <strong>[] study for example (-15.11.20${calImg})</strong>`,

    'recurring',
    `<strong>[] get groceries (every day${calImg})</strong>
    <strong>[] get groceries (today${calImg})</strong>

    <strong>[] gym (every Tuesday${calImg})</strong>
    <strong>[] team meeting (every 2nd Tuesday${calImg})</strong>
    <strong>[] project meeting (every 3rd Tuesday${calImg})</strong>
    <strong>[] company meeting (every 4th Tuesday${calImg})</strong>

    <strong>[] vacuum (every 10.${calImg})</strong>

    <strong>[] John's birthday (every 5.10${calImg})</strong>`,

    'important',
    `<strong><span style="border:solid 1px red; padding: 2px">[] pick up from airport!</span>

    <span style="border:solid 1px red; padding: 2px">[] even more important!!</span><strong>`
]

async function pic(page, name, content) {
    let dedented = content.replace(/\n {4}/g, '\n')
    await page.setContent(`
    <body style="background: #1e1e1e">
        <pre id="ele" style="display: inline-block; padding: 4px 10px; color: #d4d4d4; font-size: 14px; line-height: 150%; font-family: Helvetica">${dedented}</pre>
    </body>
    `)

    const example = await page.$('#ele')
    const boundingBox = await example.boundingBox()

    await page.screenshot({
        path: `../../images/${name}.png`,
        // omitBackground: true,
        clip: {
            x: boundingBox.x,
            y: boundingBox.y,
            width: Math.min(boundingBox.width, page.viewport().width),
            height: Math.min(boundingBox.height, page.viewport().height)
        }
    })
}

async function main() {
    const browser = await puppeteer.launch()
    const page = await browser.newPage()
    await page.setViewport({
        width: 960,
        height: 760,
        deviceScaleFactor: 1
    })

    for (let i = 0; i < samples.length; i += 2) {
        await pic(page, samples[i], samples[i + 1])
    }

    await browser.close()
}

main()
