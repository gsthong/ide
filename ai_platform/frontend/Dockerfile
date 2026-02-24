FROM node:20-slim AS base
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .

# Dev stage
FROM base AS dev
CMD ["npm", "run", "dev"]

# Build stage
FROM base AS builder
RUN npm run build

# Production stage
FROM node:20-slim AS runner
WORKDIR /app
ENV NODE_ENV production
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
EXPOSE 3000
CMD ["node", "server.js"]
