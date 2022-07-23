//webpack.config.js
const path = require('path');

module.exports = {
    mode: "development",
    devtool: "inline-source-map",
    entry: {
        main: "./src/index.ts",
    },
    output: {
        path: path.resolve(__dirname, './dist'),
        filename: "index.js",
        library: { type: "commonjs" }
    },
    resolve: {
        extensions: [".ts", ".tsx", ".js"],
    },
    externals: {
        // "date-fns": "commonjs date-fns",
        fs: "commonjs fs",
        path: "commonjs path",
    },
    module: {
        rules: [
            {
                test: /\.tsx?$/,
                loader: "ts-loader"
            }
        ]
    }
};