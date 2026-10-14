# Build context: repository root (the web app depends on packages/task-library).
FROM node:22-alpine AS build
WORKDIR /repo
COPY package.json package-lock.json ./
COPY packages/task-library/package.json packages/task-library/
COPY apps/web/package.json apps/web/
RUN npm ci --no-audit --no-fund
COPY packages/task-library packages/task-library
COPY apps/web apps/web
RUN npm run build -w apps/web

FROM nginx:1.27-alpine
COPY apps/web/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /repo/apps/web/dist /usr/share/nginx/html
