#!/bin/sh
set -e
cd /app/server
npm run migrate
# Assume docker_node_start has seeding handled
exec npm run start-worker
