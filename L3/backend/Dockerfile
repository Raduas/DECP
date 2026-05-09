FROM node:26.1.0-trixie-slim

WORKDIR /code

COPY ./package.json /code/package.json

RUN npm install

COPY ./app /code/app

CMD ["node", "app/main.js"]