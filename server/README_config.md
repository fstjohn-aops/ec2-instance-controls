# Configuration

This document describes how configuration works in this project. It was copied
from platform-accounts.

There are three forms of configuration. One subsection is devoted to each.

## 1. `.env` file

The `.env` file contains environment variables that should be set within this
project.

This file is required but gitignored. To create it, run `cp .env.sample .env`
to create one based on the sample, then fill it in according to the comments.
Make sure not to commit the `.env` file or the secrets inside of it.

**If you are just trying to get up and running quickly after cloning, you can
stop reading this document here.**

The `.env` variable becomes environment variables in the Node process and
Docker config without actually having to set environment variables on the OS
level. This is achieved by builtin Docker mechanisms and the Node module
[dotenv](https://www.npmjs.com/package/dotenv).

The `.env` file mostly affects execution by feeding into the other two forms of
config, which both have mechanisms to interpolate set environment variables.

## 2. Node server config

This takes the form of `config.*.yaml`. Defaults are included as several
committed files, such as `config.dev.yaml`.

Provided `.env`'s defaults are used, this should need no further setup. If you
want to customize values inside of it, create a `config.override.yaml`. This
override file is recursively merged into the main config file with lodash's
merge. It is gitignored, so you can set up your own environment without having
to commit anything.

In code, this config file is loaded using `src/init/ProjectConfig`. It first
decides using values in `.env` which file to load. Then it loads it and
interpolates environment variables from `.env` using the `${(env variable
name)}` syntax. (`$$` is an escaped dollar sign in case of ambiguity.) Finally,
it loads and recursively merges values from `config.override.yaml` if it
exists.

## 3. Docker config

This is `docker-compose.yml` and related files. See
[Docker's documentation](https://docs.docker.com/compose/compose-file/compose-file-v3/)
on this file format.

The `docker-compose.override.yml` that Docker looks up by default is
gitignored. If you want to alter your compose configuration without editing a
committed file, you can use that.

Alternately, `docker compose` accepts a `-f` option with the config to use, so
you can make your custom uncommitted file and pass it to that option if needed.

## Why is it so complicated?

We are attempting to support local development environments running the Node
server outside of Docker by default. But servers (or locals if they opt-in) do
run a Node server inside Docker. These two need completely different server
configs to work. The .env file got brought in to help with that.
