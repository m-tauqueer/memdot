# syntax=docker/dockerfile:1

FROM node:22-alpine AS base
WORKDIR /app
RUN corepack enable && corepack prepare pnpm@11.5.2 --activate

FROM base AS deps
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml ./
COPY tsconfig.base.json ./
COPY apps/mcp/package.json ./apps/mcp/
RUN pnpm install --filter @memdot/mcp... --frozen-lockfile

FROM base AS builder
COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/apps/mcp/node_modules ./apps/mcp/node_modules
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml tsconfig.base.json ./
COPY apps/mcp ./apps/mcp
WORKDIR /app/apps/mcp
RUN pnpm build

FROM base AS runner
RUN addgroup -g 10001 -S memdot && adduser -u 10001 -S memdot -G memdot
WORKDIR /app
ENV NODE_ENV=production
ENV MCP_ENV=production
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8100
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml ./
COPY apps/mcp/package.json ./apps/mcp/
RUN pnpm install --filter @memdot/mcp... --prod --frozen-lockfile \
  && chown -R 10001:10001 /app
COPY --from=builder --chown=10001:10001 /app/apps/mcp/dist ./apps/mcp/dist
USER 10001
WORKDIR /app/apps/mcp
EXPOSE 8100
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD wget -qO- http://127.0.0.1:8100/health/live || exit 1
CMD ["node", "dist/index.js"]
