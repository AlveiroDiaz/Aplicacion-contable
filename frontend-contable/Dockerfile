FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 3000

# Modo dev (no build de producción): prioriza que "un comando" levante todo
# el sistema sin la complejidad de build-args para NEXT_PUBLIC_API_URL, que
# Next.js necesita fijo desde antes de compilar el bundle de producción.
CMD ["npx", "next", "dev", "-H", "0.0.0.0"]
