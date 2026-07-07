# LMS frontend — Vite dev server with /api proxied to the backend container.
# Build context is the frontend/ directory (see .devcontainer/docker-compose.yml).
FROM node:22-alpine

WORKDIR /app

# Bake dependencies into the image; the source tree is bind-mounted at
# runtime with an anonymous volume shadowing /app/node_modules.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
