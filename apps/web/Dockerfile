# Stage: deps
FROM node:20-alpine AS deps

WORKDIR /app

COPY package*.json ./

RUN npm ci


# Stage: builder
FROM node:20-alpine AS builder

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules

COPY . .

RUN NEXT_STANDALONE=true npm run build


# Stage: runner
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

RUN addgroup --system nodejs && adduser --system --ingroup nodejs nextjs

COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

RUN chown -R nextjs:nodejs /app

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD wget -q http://localhost:3000/ -O /dev/null || exit 1

USER nextjs

CMD ["node", "server.js"]
