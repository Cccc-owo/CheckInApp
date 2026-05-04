FROM node:24-trixie-slim AS frontend-build

WORKDIR /app/apps/frontend

RUN corepack enable

COPY apps/frontend/package.json apps/frontend/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

COPY apps/frontend/ ./
RUN pnpm build

FROM nginx:1.27-alpine AS runtime

COPY deploy/docker/web/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=frontend-build /app/apps/frontend/dist /usr/share/nginx/html

EXPOSE 80
