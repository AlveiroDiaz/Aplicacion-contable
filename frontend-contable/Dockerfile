FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# NEXT_PUBLIC_* se inyecta en el bundle del cliente en tiempo de BUILD, no
# de arranque del contenedor. Por eso tiene que llegar como build-arg
# (ver docker-compose.yml: build.args), no solo como variable de entorno.
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

RUN npm run build

EXPOSE 3000

# Build de producción real: sin esto, "next dev" depende de un WebSocket de
# hot-reload para completar la hidratación de React, y si ese WebSocket no
# logra conectar (típico en un servidor detrás de ciertas redes/proxies),
# la página se ve bien pero ningún botón ni formulario responde a clics.
CMD ["npm", "start"]
