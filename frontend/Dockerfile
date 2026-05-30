# Прод-сборка Next.js фронтенда. pnpm install, next build, next start.
# NEXT_PUBLIC_* инлайнятся на build-time, поэтому приходят через ARG.
# Серверные секреты и BACKEND_URL подаются на runtime через env_file в compose.
FROM node:22-alpine

# В docker-сборке IPv6 до npm-реестра не маршрутизируется, Node должен предпочитать IPv4.
ENV NODE_OPTIONS=--dns-result-order=ipv4first
RUN corepack enable
WORKDIR /app

# packageManager в package.json пинит pnpm 11.5.1, corepack ставит её сам.
# pnpm-workspace.yaml несёт allowBuilds (sharp, esbuild и др.), нужен ДО install,
# иначе pnpm заблокирует build-скрипты и упадёт с ERR_PNPM_IGNORED_BUILDS.
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile

COPY . .

ARG NEXT_PUBLIC_APP_URL
ARG NEXT_PUBLIC_WS_BASE_URL
ARG NEXT_PUBLIC_BACKEND_WS_URL
ENV NEXT_PUBLIC_APP_URL=$NEXT_PUBLIC_APP_URL \
    NEXT_PUBLIC_WS_BASE_URL=$NEXT_PUBLIC_WS_BASE_URL \
    NEXT_PUBLIC_BACKEND_WS_URL=$NEXT_PUBLIC_BACKEND_WS_URL \
    NEXT_TELEMETRY_DISABLED=1 \
    NODE_ENV=production

# Плейсхолдеры только для пререндера на build-time (better-auth не терпит дефолтный секрет).
# На runtime env_file из compose перебивает эти значения реальными.
ENV BETTER_AUTH_SECRET=build-time-placeholder \
    BETTER_AUTH_URL=http://localhost:3000 \
    BACKEND_URL=http://localhost:8000

RUN pnpm build

EXPOSE 3000
CMD ["pnpm", "start"]
