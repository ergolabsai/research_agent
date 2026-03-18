# =============================================================================
# Multi-stage Frontend Dockerfile
# Targets: prod (nginx), dev (vite dev server)
# =============================================================================

# ---------------------------------------------------------------------------
# Stage: deps — install node_modules (cached layer)
# ---------------------------------------------------------------------------
FROM node:20-alpine AS deps
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci

# ---------------------------------------------------------------------------
# Stage: build — compile TypeScript and bundle with Vite
# ---------------------------------------------------------------------------
FROM deps AS build
COPY frontend/ .
RUN npm run build

# ---------------------------------------------------------------------------
# Target: prod — serve built assets via nginx
# ---------------------------------------------------------------------------
FROM nginx:alpine AS prod

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 5173

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget -qO- http://localhost:5173/ || exit 1

CMD ["nginx", "-g", "daemon off;"]

# ---------------------------------------------------------------------------
# Target: dev — Vite dev server with HMR
# ---------------------------------------------------------------------------
FROM deps AS dev

COPY frontend/ .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
