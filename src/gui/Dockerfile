# Base image
FROM node:14-alpine as base

# https://github.com/MrRio/jsPDF/issues/2208
RUN apk update && apk add --no-cache bash git openssh

COPY package*.json ./


# Build stage
FROM base as builder

RUN npm ci

COPY . .
RUN npm run build


# Deployment stage
FROM base as app

WORKDIR /usr/src/app
ENV NODE_ENV=production

# Installing production dependencies only (NODE_ENV)
COPY package*.json ./
RUN npm ci

COPY server.js ./
COPY public ./public

# Copy built files
COPY --from=builder .next ./.next

USER node
EXPOSE 3000
CMD [ "npm", "run", "start" ]