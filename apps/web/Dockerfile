FROM node:22-bookworm-slim
WORKDIR /app/apps/web
COPY apps/web/package*.json ./
RUN npm ci
COPY apps/web/ ./
COPY scripts/lib/env.mjs /app/scripts/lib/env.mjs
COPY scripts/web.mjs /app/scripts/web.mjs
ENV NEXT_TELEMETRY_DISABLED=1
ARG API_URL=http://api:8000
ENV API_URL=$API_URL
ENV WEB_HOST=0.0.0.0
RUN npm run build && chown -R node:node /app/apps/web/.next
USER node
EXPOSE 3000
CMD ["npm", "start"]
