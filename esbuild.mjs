import * as esbuild from "esbuild"

await esbuild.build({
    entryPoints: [
        "./client-src/about/index.css",
        "./client-src/base/base.css",
        "./client-src/base/base.js",
        "./client-src/case-studies/index.css",
        "./client-src/create/index.js",
        "./client-src/create-results/index.js",
        "./client-src/digitize/index.js",
        "./client-src/digitize-results/index.js",
        "./client-src/help/index.css",
        "./client-src/help/index.js",
        "./client-src/index/index.css",
        "./client-src/pico/pico.css",
    ],
    entryNames: "[dir]", // will name the result files by their folder names
    outbase: "./client-src",
    bundle: true,
    minify: true,
    sourcemap: "linked",
    outdir: "./sketch_map_tool/static/bundles",
    format: "esm",
    external: [
        "/static/assets/*",
    ],
})
