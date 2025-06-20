#!/bin/sh

failures=0

echo "---"
echo "Running server checks"
echo "---"
echo "cd /app/server"
cd /app/server
# This only makes sense if run as part of a docker compose up
sh wait-for.sh postgres_test:5432
echo "npm run migrate"
npm run migrate
echo "npm run check"
npm run check
if [ $? -ne 0 ]; then
    failures=1
fi

exit $failures