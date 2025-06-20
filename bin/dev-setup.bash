#!/bin/env bash

# This script is used to setup the development environment.
# It contains some TODOs for future automations.

# -e: exit on error
# -u: exit on undefined variable
# -o pipefail: exit on pipe failure
set -eou pipefail

# Check if the user has the necessary development tools installed.
function check_dev_tools() {
	local missing=()
	declare -A instructions
	instructions=(
		["trove"]="Please install it from https://github.com/aops-ba/trove"
		["docker"]="Please install it from https://www.docker.com/"
	)

	echo "Checking development tools..." >&2
	echo >&2

	# Check if trove CLI is installed
	if ! command -v trove &>/dev/null; then
		missing+=("trove")
	fi

	# Check if Docker is installed
	if ! command -v docker &>/dev/null; then
		missing+=("docker")
	fi

	for requirement in "${missing[@]}"; do
		echo "  ❌ Missing requirement: $requirement" >&2
		echo "     - ${instructions[$requirement]}" >&2
	done

	if [ ${#missing[@]} -eq 0 ]; then
		echo "  ✅ All development tools are installed." >&2
	fi
}

function copy_env_files() {
	echo "Checking environment files..." >&2
	echo >&2

	# Copy server/.env.sample to server/.env if it doesn't exist.
	if [ ! -f server/.env ]; then
		cp server/.env.sample server/.env
		echo "  ✨ Created server/.env" >&2
		echo "     - Please fill in values manually." >&2
		echo >&2
	else
		echo "  ✅ server/.env already exists." >&2
		echo >&2
	fi

	# Check if server/.env is using the default COMPOSE_PROJECT_NAME (fastack_starter_server)
	if grep -q "fastack_starter_server" server/.env; then
		echo "  ❌ server/.env is using the default COMPOSE_PROJECT_NAME (fastack_starter_server)." >&2
		echo "     - Please change COMPOSE_PROJECT_NAME to <your-project-name>_server" >&2
		echo >&2
	else
		echo "  ✅ server/.env is using a non-default COMPOSE_PROJECT_NAME." >&2
		echo >&2
	fi

	# Check if server/.env has SECRET_PLATFORM_API_KEY set
	local server_platform_key
	server_platform_key=$(grep "SECRET_PLATFORM_API_KEY" server/.env | cut -d= -f2 | tr -d ' ')

	if [ -z "$server_platform_key" ]; then
		echo "  ❌ server/.env SECRET_PLATFORM_API_KEY is missing or empty" >&2
		echo "     - Please set this value." >&2
		echo >&2
	else
		echo "  ✅ server/.env SECRET_PLATFORM_API_KEY is set." >&2
		echo >&2
	fi

	# Check if server/.env has SECRET_DATABASE_PASSWORD set
	local server_db_pwd
	server_db_pwd=$(grep "SECRET_DATABASE_PASSWORD" server/.env | cut -d= -f2 | tr -d ' ')

	if [ -z "$server_db_pwd" ]; then
		echo "  ❌ server/.env SECRET_DATABASE_PASSWORD is missing or empty" >&2
		echo "     - Please set this value." >&2
		echo >&2
	else
		echo "  ✅ server/.env SECRET_DATABASE_PASSWORD is set." >&2
		echo >&2
	fi

	# Copy nextjs/.env.sample to nextjs/.env.local if it doesn't exist.
	if [ ! -f nextjs/.env.local ]; then
		cp nextjs/.env.local.sample nextjs/.env.local
		echo "  ✨ Created nextjs/.env.local" >&2
		echo "     - Please fill in values manually." >&2
		echo >&2
	else
		echo "  ✅ nextjs/.env.local already exists." >&2
		echo >&2
	fi

	# Check if nextjs/.env is using the default APPLICATION_CODE (fastackstarter)
	if grep -q "fastackstarter" nextjs/.env; then
		echo "  ❌ nextjs/.env is using the default APPLICATION_CODE (fastackstarter)." >&2
		echo "     - Please change APPLICATION_CODE to <your-project-name>" >&2
		echo >&2
	else
		echo "  ✅ nextjs/.env is using a non-default APPLICATION_CODE." >&2
		echo >&2
	fi

	# Check if nextjs/.env.local has SECRET_PLATFORM_API_KEY set
	local next_platform_key
	next_platform_key=$(grep "SECRET_PLATFORM_API_KEY" nextjs/.env.local | cut -d= -f2 | tr -d ' ')

	if [ -z "$next_platform_key" ]; then
		echo "  ❌ nextjs/.env.local SECRET_PLATFORM_API_KEY is missing or empty" >&2
		echo "     - Please set this value." >&2
		echo >&2
	else
		echo "  ✅ nextjs/.env.local SECRET_PLATFORM_API_KEY is set." >&2
		echo >&2
	fi

	# Check if nextjs/.env.local has SECRET_COOKIE_SIGNATURE_KEY set
	local next_cookie_key
	next_cookie_key=$(grep "SECRET_COOKIE_SIGNATURE_KEY" nextjs/.env.local | cut -d= -f2 | tr -d ' ')

	if [ -z "$next_cookie_key" ]; then
		echo "  ❌ nextjs/.env.local SECRET_COOKIE_SIGNATURE_KEY is missing or empty" >&2
		echo "     - Please set this value." >&2
		echo >&2
	else
		echo "  ✅ nextjs/.env.local SECRET_COOKIE_SIGNATURE_KEY is set." >&2
		echo >&2
	fi

	# Check if nextjs/.env.local has LAUNCHDARKLY_SDK_KEY set
	local next_launchdarkly_key
	next_launchdarkly_key=$(grep "LAUNCHDARKLY_SDK_KEY" nextjs/.env.local | cut -d= -f2 | tr -d ' ')

	if [ -z "$next_launchdarkly_key" ]; then
		echo "  ❌ nextjs/.env.local LAUNCHDARKLY_SDK_KEY is missing or empty" >&2
		echo "     - Please set this value." >&2
		echo >&2
	else
		echo "  ✅ nextjs/.env.local LAUNCHDARKLY_SDK_KEY is set." >&2
		echo >&2
	fi

	# Check matching values between server and nextjs
	local next_api_key
	local server_api_key
	next_api_key=$(grep "SECRET_FASTACK_STARTER_API_KEY" nextjs/.env.local | cut -d= -f2 | tr -d ' ')
	server_api_key=$(grep "SECRET_FASTACK_STARTER_API_KEY" server/.env | cut -d= -f2 | tr -d ' ')

	if [ -z "$next_api_key" ] || [ -z "$server_api_key" ]; then
		echo "  ❌ SECRET_FASTACK_STARTER_API_KEY is empty in one or both files." >&2
		echo "     - Please set this value in nextjs/.env.local and server/.env" >&2
		echo >&2
	elif [ "$next_api_key" != "$server_api_key" ]; then
		echo "  ❌ SECRET_FASTACK_STARTER_API_KEY values don't match." >&2
		echo "     - Please ensure value is identical in nextjs/.env.local and server/.env" >&2
		echo >&2
	else
		echo "  ✅ SECRET_FASTACK_STARTER_API_KEY matches and is not empty." >&2
		echo >&2
	fi

	# Check if nextjs/.env.local REDIS_PASSWORD matches the server/.env REDIS_PASSWORD
	local next_redis_pwd
	local server_redis_pwd
	next_redis_pwd=$(grep "REDIS_PASSWORD" nextjs/.env.local | cut -d= -f2 | tr -d ' ')
	server_redis_pwd=$(grep "REDIS_PASSWORD" server/.env | cut -d= -f2 | tr -d ' ')

	if [ -z "$next_redis_pwd" ] || [ -z "$server_redis_pwd" ]; then
		echo "  ❌ REDIS_PASSWORD is empty in one or both files." >&2
		echo "     - Please set this value in nextjs/.env.local and server/.env" >&2
		echo >&2
	elif [ "$next_redis_pwd" != "$server_redis_pwd" ]; then
		echo "  ❌ REDIS_PASSWORD values don't match." >&2
		echo "     - Please ensure value is identical in nextjs/.env.local and server/.env" >&2
		echo >&2
	else
		echo "  ✅ REDIS_PASSWORD matches and is not empty." >&2
		echo >&2
	fi

	# TODO: Add a script to fill in the .env files magically.
	# That'll probably involve using Phase and/or something else.
}
function next_steps() {
	# TODO: Figure out how to reliably check if the DB is initialized
	# automatically so this is not a manual step.
	echo "🚀 You're almost ready to develop!" >&2
	echo >&2
	echo "  1. Fill in server/.env and nextjs/.env.local" >&2
	echo "  2. Run \`npm run reset-db\` to initialize PostgreSQL." >&2
	echo "  3. Run \`npm run dev\` to start Fastify, Next.js, PostgreSQL, and Redis." >&2
}

# Initialize the development environment.
function dev_setup() {
	# Determine terminal width for pretty dividers.
	local term_width
	term_width=$(tput cols)
	local divider
	divider=$'\n'"$(printf '\033[34m━%.0s\033[0m' $(seq 1 "$term_width"))"$'\n'

	echo "$divider" >&2
	echo "🔧 Initializing Fastack development environment..." >&2
	echo "$divider" >&2

	# Setup VSCode settings.
	npx tsx setupVSCodeSettings.ts
	echo "$divider" >&2

	# Check if the user has the necessary development tools installed.
	check_dev_tools
	echo "$divider" >&2

	# Copy the environment files.
	copy_env_files
	echo "$divider" >&2

	# Print remaining manual steps.
	next_steps
	echo "$divider" >&2

	# Exit successfully.
	exit 0
}

dev_setup
