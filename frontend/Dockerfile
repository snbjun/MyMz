FROM node:22-alpine

WORKDIR /app/frontend

COPY package*.json ./
RUN npm ci

COPY index.html ./
COPY tsconfig.json tsconfig.node.json vite.config.ts ./
COPY src ./src

EXPOSE 8080

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "8080"]
