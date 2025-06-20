#!/bin/sh

failures=0

echo "---"
echo "Running nextjs checks"
echo "---"
echo "cd /app/nextjs"
cd /app/nextjs
echo "npm run check"
npm run check
if [ $? -ne 0 ]; then
    failures=1
fi

exit $failures