/* eslint-disable import/no-extraneous-dependencies */
require("esbuild")
    .build({
        entryPoints: [
            "./client-src/create/index.js",
            "./client-src/create-results/index.js",
        ],
        entryNames: "[dir]",
        outbase: "./client-src",
        bundle: true,
        outdir: "./sketch_map_tool/static/bundles",
        format: "esm",
        minify: true,
    }).catch(() => process.exit(1));
/* eslint-enable */
