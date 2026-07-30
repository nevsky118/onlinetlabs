# Multi-stage monorepo build. turbo prune emits a pruned lockfile so a sibling app's
# dependency change does not invalidate the install layer.
FROM node:22-alpine AS base
ENV NODE_OPTIONS=--dns-result-order=ipv4first
RUN corepack enable
WORKDIR /app

FROM base AS prepare
COPY . .
# Global `pnpm add -g` needs PNPM_HOME/bin on PATH and fails without it, so use dlx
RUN pnpm dlx turbo@^2 prune web --docker

FROM base AS builder
COPY --from=prepare /app/out/json/ .
RUN pnpm install --frozen-lockfile
COPY --from=prepare /app/out/full/ .

# Marketing image, public origin vars only, no secrets
ARG NEXT_PUBLIC_WEB_URL
ARG NEXT_PUBLIC_APP_URL
ARG NEXT_PUBLIC_AUTH_URL
ARG NEXT_PUBLIC_WS_BASE_URL
ARG NEXT_PUBLIC_ANALYTICS_URL
ENV NEXT_PUBLIC_WEB_URL=$NEXT_PUBLIC_WEB_URL \
    NEXT_PUBLIC_APP_URL=$NEXT_PUBLIC_APP_URL \
    NEXT_PUBLIC_AUTH_URL=$NEXT_PUBLIC_AUTH_URL \
    NEXT_PUBLIC_WS_BASE_URL=$NEXT_PUBLIC_WS_BASE_URL \
    NEXT_PUBLIC_ANALYTICS_URL=$NEXT_PUBLIC_ANALYTICS_URL \
    NEXT_TELEMETRY_DISABLED=1 \
    NODE_ENV=production
RUN pnpm turbo build --filter=web

FROM base AS runner
ENV NODE_ENV=production
# standalone server.js defaults to 3000, web runs on 3001
ENV PORT=3001
COPY --from=builder /app/apps/web/.next/standalone ./
COPY --from=builder /app/apps/web/.next/static ./apps/web/.next/static
COPY --from=builder /app/apps/web/public ./apps/web/public
EXPOSE 3001
CMD ["node", "apps/web/server.js"]
