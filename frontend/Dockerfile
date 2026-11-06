# ---- Frontend Dockerfile (multi‑stage) ----
# Builder stage
FROM node:20-alpine AS builder
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# Production stage (nginx)
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
# Optional: copy custom nginx config
# COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s \
  CMD wget -qO- http://localhost || exit 1

CMD ["nginx", "-g", "daemon off;"]

