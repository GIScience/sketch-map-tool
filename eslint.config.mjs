import { defineConfig, globalIgnores } from "eslint/config"
import globals from "globals"
import { importX } from "eslint-plugin-import-x"
import { createTypeScriptImportResolver } from "eslint-import-resolver-typescript"
import tseslint from "typescript-eslint" // step 3

export default defineConfig([
    globalIgnores([
        "sketch_map_tool/static/",
        "**/node_modules/*",
        ".venv/"
    ]),

    {
        files: ["**/*.{js,mjs,ts}"],
        extends: [importX.flatConfigs.recommended],
        languageOptions: {
            globals: {
                ...globals.browser,
            },
            ecmaVersion: "latest",
            sourceType: "module",
        },
        settings: {
            "import-x/resolver-next": [createTypeScriptImportResolver()],
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
            "import-x/prefer-default-export": "off",
            "import-x/extensions": "off",
        },
    },

    {
        files: ["**/*.ts"],
        extends: [tseslint.configs.recommended, importX.flatConfigs.typescript],
        rules: {
            // swap core rules for their TypeScript-aware versions
            "no-unused-vars": "off",
            "@typescript-eslint/no-unused-vars": "warn",
            "no-shadow": "off",
            "@typescript-eslint/no-shadow": "warn",
        },
    },

])
