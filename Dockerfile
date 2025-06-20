# NOTE: We would've put this Dockerfile in the /server directory
# except we need to copy files from nextjs when running node inside
# docker, so...Dockerfile is living in this root directory.

#
# serverbase - helper stage, starts steps for server/
#
FROM node:22-alpine AS serverbase
LABEL "com.aops.application"="fastack-starter"
WORKDIR /app/server

ARG TROVE_AWS_ACCESS_KEY_ID
ARG TROVE_AWS_SECRET_ACCESS_KEY
RUN echo ${TROVE_AWS_ACCESS_KEY_ID}
ENV AWS_ACCESS_KEY_ID=${TROVE_AWS_ACCESS_KEY_ID}
ENV AWS_SECRET_ACCESS_KEY=${TROVE_AWS_SECRET_ACCESS_KEY}
ENV AWS_DEFAULT_REGION=us-east-1

RUN apk update && apk add aws-cli

# Copy the bare minimum needed for npm install to improve caching.
COPY server/package.json server/package-lock.json ./

# Run this right before npm install, due to caching shenanigans. The login
# here expires in 12 hours, but Docker builds will cache it. If we're still
# using the cache at this point, with a maybe invalid login, presumably npm
# install is cached too and it won't matter.
RUN aws codeartifact login --tool npm --repository aops --domain aops --domain-owner 865917575078 --namespace @aops-trove
RUN npm i

# Copy only what is needed for building Typescript.
COPY server/src src
COPY server/tsconfig* ./
RUN npm install copyfiles -g
RUN npm run build


#
# nextjsbase - helper stage, starts steps for nextjs/
# Separate from server/ steps so that npm install caching is separate.
# Stops short of actual build so that dev/prod can share it.
#
FROM node:22-alpine AS nextjsbase
WORKDIR /app/nextjs

ARG TROVE_AWS_ACCESS_KEY_ID
ARG TROVE_AWS_SECRET_ACCESS_KEY
ENV AWS_ACCESS_KEY_ID=${TROVE_AWS_ACCESS_KEY_ID}
ENV AWS_SECRET_ACCESS_KEY=${TROVE_AWS_SECRET_ACCESS_KEY}
ENV AWS_DEFAULT_REGION=us-east-1

RUN apk update && apk add aws-cli

# Copy the bare minimum needed for npm install to improve caching.
COPY nextjs/package.json nextjs/package-lock.json ./

RUN aws codeartifact login --tool npm --repository aops --domain aops --domain-owner 865917575078 --namespace @aops-trove
RUN npm install
COPY nextjs/.env ./.env
COPY nextjs/next.config* nextjs/middleware.ts nextjs/tsconfig.json nextjs/.eslintrc.json nextjs/.prettierrc nextjs/.prettierignore ./
COPY nextjs/app app
COPY nextjs/components components
COPY nextjs/lib lib
COPY nextjs/public public
RUN npm run build

#
# ci - container stage, used by ci for running tests
# depends on base
#
FROM node:22-alpine AS ci
LABEL "com.aops.application"="fastack-starter"
WORKDIR /app

# Copy npm modules, build output first for caching.

COPY --from=serverbase /app/server/node_modules server/node_modules
COPY --from=serverbase /app/server/tsout server/tsout
COPY --from=nextjsbase /app/nextjs/node_modules nextjs/node_modules

COPY server server
COPY nextjs nextjs

COPY docker_node_ci_codegen.sh docker_node_ci_nextjs.sh docker_node_ci_server.sh wait-for.sh ./

# Helps implement IS_DOCKER in src/util/General
RUN echo "" > server/.isdocker

RUN chmod 755 docker_node_ci_codegen.sh docker_node_ci_nextjs.sh docker_node_ci_server.sh wait-for.sh

# Only run the main script once Postgres is ready using the wait-for utility.
CMD [ "sh", "./wait-for.sh", "postgres_test:5432", "--", "sh", "/app/docker_node_ci.sh" ]


#
# runtimefiles - helper stage, contains all files needed to run real server
# depends on base
#
FROM node:22-alpine AS runtimefiles
LABEL "com.aops.application"="fastack-starter"
WORKDIR /app

# Copy npm modules, build output first for caching.

COPY --from=serverbase /app/server/node_modules server/node_modules
COPY --from=serverbase /app/server/tsout server/tsout

COPY server/config*.yaml server/package.json server/package-lock.json server/knexfile.ts server/
COPY server/migrations server/migrations
COPY server/seeds server/seeds

# TODO: needed by knexfile, would rather not have to copy it though
COPY --from=serverbase /app/server/src server/src

COPY docker_node_start.sh docker_node_worker.sh wait-for.sh ./

# Helps implement IS_DOCKER in src/util/General
RUN echo "" > server/.isdocker


#
# prodworker - container stage, runs worker-mode server for prod or staging
# depends on runtimefiles
#
FROM runtimefiles AS prodworker
LABEL "com.aops.application"="fastack-starter"
WORKDIR /app

RUN chmod 755 docker_node_worker.sh

CMD [ "sh", "/app/docker_node_worker.sh" ]


#
# devworker - container stage, runs worker-mode server for dev
# depends on runtimefiles
#
FROM runtimefiles AS devworker
LABEL "com.aops.application"="fastack-starter"
WORKDIR /app

RUN chmod 755 docker_node_worker.sh wait-for.sh

CMD [ "sh", "./wait-for.sh", "postgres:5432", "--", "sh", "/app/docker_node_worker.sh" ]


#
# prod - container stage, runs server in a prod/staging environment
# depends on runtimefiles
#
FROM runtimefiles AS prod
LABEL "com.aops.application"="fastack-starter"
WORKDIR /app

RUN chmod 755 docker_node_start.sh

# docker_node_start has our startup commands.
CMD [ "sh", "/app/docker_node_start.sh" ]


#
# dev - container stage, runs server in a dev environment
# depends on runtimefiles
#
FROM runtimefiles AS dev
LABEL "com.aops.application"="fastack-starter"
WORKDIR /app

RUN chmod 755 docker_node_start.sh wait-for.sh

# docker_node_start has our startup commands, but only run it once Postgres is
# ready using the wait-for utility.
CMD [ "sh", "./wait-for.sh", "postgres:5432", "--", "sh", "/app/docker_node_start.sh" ]
