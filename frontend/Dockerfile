# ---- build the React app ----
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install --no-audit --no-fund
COPY . .
# The browser (not the container) calls the API, so this is the address of the API as seen from your computer.
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL
# vite build only: the strict type check is `npm run build`, kept out of the container build on purpose
RUN npx vite build

# ---- serve it with nginx ----
FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
