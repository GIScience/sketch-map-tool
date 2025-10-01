import * as esbuild from "esbuild"

await esbuild.build({
    entryPoints: [
        "./client-src/pico/pico.css",
        "./client-src/base/base.css",
        "./client-src/base/base.js",
        "./client-src/index/index.css",
        "./client-src/help/index.css",
        "./client-src/help/index.js",
        "./client-src/about/index.css",
        "./client-src/case-studies/index.css",
        "./client-src/create/index.js",
        "./client-src/create-results/index.js",
        "./client-src/digitize/index.js",
        "./client-src/digitize-results/index.js",
    ],
    entryNames: "[dir]", // will name the result files by their folder names
    outbase: "./client-src",
    bundle: true,
    minify: true,
    outdir: "./sketch_map_tool/static/bundles",
    format: "esm",
    external: [
        "/static/assets/*",
    ],
})
