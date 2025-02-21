FROM node:18-alpine

WORKDIR /frontend

COPY package*.json ./

RUN npm install

ENV NODE_ENV=development

COPY src/ src/

COPY public/ public/

EXPOSE 5000

CMD ["npm", "run", "serve"]
