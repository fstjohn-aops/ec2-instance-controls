#!/bin/sh
failures=0

echo "---"
echo "Verifying server codegen is up-to-date."
echo "To fix failures here, 'npm run gen-all' and commit the result."
echo "---"
echo "cd /app/server"
cd /app/server
# This only makes sense if run as part of a docker compose up
sh wait-for.sh postgres:5432
echo "npm run migrate"
npm run migrate
# All of the codegen steps that your repo runs go here.
echo "npx tsx tools/genBulkImports.ts --check --diff"
npx tsx tools/genBulkImports.ts --check --diff
echo "npx tsx tools/genTsKnex.ts --check --diff"
npx tsx tools/genTsKnex.ts --check --diff
echo "npx tsx tools/syncDirs.ts --json sync_dirs_config.json --check"
npx tsx tools/syncDirs.ts --json sync_dirs_config.json --check
if [ $? -ne 0 ]; then
    failures=1
fi
exit $failures