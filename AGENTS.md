# Project notes

## Frontend code style (enforced by prettier + oxlint)

- No semicolons, double quotes, LF, trailing commas (es5), width 100
- Blank line between JSX sibling blocks and logical code groups
- No comments in code unless asked
- Types/interfaces always in a separate `types.ts` next to the slice
  (or `shared/types/` for cross-slice types)
- Imports sorted alphabetically by path (prettier-plugin-organize-imports)
- FSD layers: app > pages > widgets > features > entities > shared;
  imports only downwards
- Commands: `npm run format`, `npm run lint`, `npm run format:check`
