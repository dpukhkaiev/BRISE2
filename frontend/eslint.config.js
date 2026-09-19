import js from "@eslint/js";
import globals from "globals";
import pluginVue from "eslint-plugin-vue";
import vueParser from "vue-eslint-parser";
import boundaries from "eslint-plugin-boundaries";
import tsParser from "@typescript-eslint/parser";

const supportedFiles = ["**/*.{js,mjs,cjs,jsx,ts,tsx,vue}"];

export default [
    {
        ignores: ["**/node_modules/", "**/dist/", "**/build/", "**/vite.config.*"]
    },
    {
        files: supportedFiles,
        rules: js.configs.recommended.rules,
    },
    ...pluginVue.configs["flat/recommended"],
    {
        files: supportedFiles,
        languageOptions: {
            parser: vueParser,
            parserOptions: {
                parser: tsParser,
                ecmaVersion: "latest",
                sourceType: "module",
                extraFileExtensions: [".vue"],
            },
            globals: {
                ...globals.browser,
                ...globals.node,
            },
        },
        plugins: { boundaries },
        settings: {
            "boundaries/elements": [
                { type: "app", pattern: "src/app/*" },
                { type: "pages", pattern: "src/pages/*" },
                { type: "widgets", pattern: "src/widgets/*" },
                { type: "features", pattern: "src/features/*" },
                { type: "entities", pattern: "src/entities/*" },
                { type: "shared", pattern: "src/shared/*" },
            ],
        },
        rules: {
            "boundaries/element-types": ["error", {
                default: "disallow",
                rules: [
                    { from: "pages", allow: ["widgets", "features", "entities", "shared"] },
                    { from: "widgets", allow: ["features", "entities", "shared"] },
                    { from: "features", allow: ["entities", "shared"] },
                    { from: "entities", allow: ["shared"] },
                ],
            }],
        },
    },
];