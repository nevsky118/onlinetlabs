# Multi-stage monorepo build. turbo prune emits a pruned lockfile so a sibling app's
# dependency change does not invalidate the install layer.
FROM node:22-alpine AS base
ENV NODE_OPTIONS=--dns-result-order=ipv4first
RUN corepack enable
WORKDIR /app

FROM base AS prepare
COPY . .
# Global `pnpm add -g` needs PNPM_HOME/bin on PATH and fails without it, so use dlx
RUN pnpm dlx turbo@^2 prune dashboard --docker

FROM base AS builder
COPY --from=prepare /app/out/json/ .
RUN pnpm install --frozen-lockfile
COPY --from=prepare /app/out/full/ .

ARG NEXT_PUBLIC_WEB_URL
ARG NEXT_PUBLIC_APP_URL
ARG NEXT_PUBLIC_AUTH_URL
ARG NEXT_PUBLIC_WS_BASE_URL
ENV NEXT_PUBLIC_WEB_URL=$NEXT_PUBLIC_WEB_URL \
    NEXT_PUBLIC_APP_URL=$NEXT_PUBLIC_APP_URL \
    NEXT_PUBLIC_AUTH_URL=$NEXT_PUBLIC_AUTH_URL \
    NEXT_PUBLIC_WS_BASE_URL=$NEXT_PUBLIC_WS_BASE_URL \
    NEXT_TELEMETRY_DISABLED=1 \
    NODE_ENV=production

# Build-time prerender placeholders, overridden at runtime by env_file
ENV BETTER_AUTH_SECRET=build-time-placeholder \
    BETTER_AUTH_URL=http://localhost:3000 \
    BACKEND_URL=http://build-time-placeholder.invalid \
    INTERNAL_API_TOKEN=build-time-placeholder
RUN pnpm turbo build --filter=dashboard

FROM base AS runner
ENV NODE_ENV=production
COPY --from=builder /app/apps/dashboard/.next/standalone ./
COPY --from=builder /app/apps/dashboard/.next/static ./apps/dashboard/.next/static
COPY --from=builder /app/apps/dashboard/public ./apps/dashboard/public
EXPOSE 3000
CMD ["node", "apps/dashboard/server.js"]
