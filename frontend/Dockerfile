# Stage 1: Base
FROM node:18-alpine AS base

WORKDIR /frontend

COPY package*.json ./

RUN npm install

# Stage 2: Development
FROM base AS development

ENV NODE_ENV=development

COPY src/ src/

COPY public/ public/

EXPOSE 5000

CMD ["npm", "run", "serve"]
