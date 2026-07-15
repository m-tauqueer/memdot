import eslint from "@eslint/js";
import tseslint from "typescript-eslint";

export default tseslint.config(
  eslint.configs.recommended,
  ...tseslint.configs.recommended,
  {
    ignores: ["dist/**", "node_modules/**", "coverage/**"],
  },
  {
    rules: {
      "no-restricted-imports": [
        "error",
        {
          patterns: [
            {
              group: ["**/services/**", "**/packages/domain-python/**", "**/apps/mcp/**"],
              message: "UI package must stay frontend-only.",
            },
          ],
        },
      ],
    },
  },
);
