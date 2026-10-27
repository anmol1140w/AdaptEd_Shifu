FROM node:22-alpine AS build
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
ARG VITE_GOOGLE_OAUTH_ENABLED=false
ENV VITE_API_BASE_URL=/api/v1 \
    VITE_GOOGLE_OAUTH_ENABLED=${VITE_GOOGLE_OAUTH_ENABLED}
RUN npm run build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
