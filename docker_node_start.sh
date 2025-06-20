#!/bin/sh
set -e
cd /app/server
npm run migrate
npm run seed
exec npm run start
