# syntax=docker/dockerfile:1

FROM node:22-alpine AS base
WORKDIR /app
RUN corepack enable && corepack prepare pnpm@11.5.2 --activate

FROM base AS deps
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml ./
COPY tsconfig.base.json ./
COPY apps/web/package.json ./apps/web/
RUN pnpm install --filter @memdot/web... --frozen-lockfile

FROM base AS builder
COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/apps/web/node_modules ./apps/web/node_modules
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml tsconfig.base.json ./
COPY apps/web ./apps/web
WORKDIR /app/apps/web
RUN pnpm build

FROM base AS runner
ARG MEMDOT_SOURCE_HASH=unknown
LABEL memdot.source_hash=$MEMDOT_SOURCE_HASH
RUN addgroup -g 10001 -S memdot && adduser -u 10001 -S memdot -G memdot
WORKDIR /app
ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME=0.0.0.0
COPY --from=builder --chown=10001:10001 /app/apps/web/.next/standalone ./
COPY --from=builder --chown=10001:10001 /app/apps/web/.next/static ./apps/web/.next/static
COPY --from=builder --chown=10001:10001 /app/apps/web/public ./apps/web/public
USER 10001
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s --start-period=15s --retries=3 \
  CMD wget -qO- http://127.0.0.1:3000/api/health || exit 1
CMD ["node", "apps/web/server.js"]
