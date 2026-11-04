import { defineConfig, globalIgnores } from "eslint/config"
import globals from "globals"
import importPlugin from "eslint-plugin-import"

export default defineConfig([
    globalIgnores([
        "sketch_map_tool/static/libs/",
        "sketch_map_tool/static/bundles/",
        "**/node_modules/*",
        ".venv/"
    ]),
    {
        plugins: {
            import: importPlugin,
        },
        languageOptions: {
            globals: {
                ...globals.browser,
            },
            ecmaVersion: "latest",
            sourceType: "module",
        },
        rules: {
            indent: ["error", 4, { SwitchCase: 1 }],
            quotes: ["error", "double"],
            "object-curly-spacing": ["warn", "always", {
                objectsInObjects: false,
                arraysInObjects: false,
            }],
            "no-unused-vars": "warn",
            "no-plusplus": "off",
            "no-shadow": "warn",
            "no-underscore-dangle": "warn",
            "prefer-template": "warn",
            "no-undef": "warn",
            "import/prefer-default-export": "off",
            "import/extensions": "off",
        },
    },
])
