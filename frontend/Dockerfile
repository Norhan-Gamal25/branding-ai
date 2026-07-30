# Branding AI — Frontend Dockerfile (multi-stage)

# ── Stage 1: Build ───────────────────────────────────────────────────────────
FROM node:20-alpine AS builder
WORKDIR /app

# Install deps first (layer-cached unless package files change)
COPY package.json package-lock.json ./
RUN npm ci --prefer-offline

COPY . .

# BACKEND_URL is read at build time by Next.js for the standalone bundle
ARG BACKEND_URL=http://backend:8000
ENV BACKEND_URL=$BACKEND_URL

# Ensure public/ exists so the COPY in the runner stage never fails
RUN mkdir -p public

RUN npm run build

# ── Stage 2: Minimal runtime ─────────────────────────────────────────────────
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV HOSTNAME=0.0.0.0
ENV PORT=3000

# Copy only the standalone output
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static     ./.next/static
COPY --from=builder /app/public           ./public/

EXPOSE 3000
CMD ["node", "server.js"]
