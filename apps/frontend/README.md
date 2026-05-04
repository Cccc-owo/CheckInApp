# CheckIn App Frontend

Vue 3 + TypeScript frontend for CheckIn App. This is the supported frontend source tree.

## Commands

```bash
pnpm install
pnpm dev
pnpm lint:check
pnpm test
pnpm build
```

The development server runs on port `3000` and proxies `/api` to `http://127.0.0.1:8000`.

## Structure

- `src/app/`: auth state, router, theme state
- `src/api/`: typed API helpers and fetch client
- `src/components/ui/`: shadcn-vue primitives
- `src/components/templates/`: structured template field editor
- `src/views/`: route-owned pages
- `src/style.css`: Tailwind v4 and shadcn token setup

Prefer shadcn-vue primitives, lucide icons, semantic tokens, and the local helpers in `src/components/ui.ts` for repeated surfaces. Keep route-local Tailwind where it expresses one-off layout or dense operational structure.
