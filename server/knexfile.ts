// This file is present so knex migrate:X knows how to connect.

import {Knex} from "knex";
import {
	initProjectConfig,
	ProjectConfig,
	ProjectDbConfig,
} from "./src/init/ProjectConfig";

function makeKnexConfig(baseConfig: ProjectDbConfig): Knex.Config {
	return {
		client: "pg",
		connection: {
			host: baseConfig.host,
			port: baseConfig.port || 5432,
			database: baseConfig.dbname,
			user: baseConfig.user,
			password: baseConfig.password,
		},
		pool: {
			min: baseConfig.poolMin || 1,
			max: baseConfig.poolMax || 1,
		},
		migrations: {
			tableName: "knex_migrations",
			extension: "ts",
		},
	};
}

const config: ProjectConfig = initProjectConfig();

const exp: {[env: string]: Knex.Config} = {};

if (typeof config.serverDb === "string") {
	const mainConfig = config.db[config.serverDb];
	if (mainConfig) {
		exp.main = {
			...makeKnexConfig(mainConfig),
		};
	} else {
		console.error(
			"WARNING: " +
				"config serverDb is a string not pointing to a config db entry. " +
				"knex migrate with --env main will not work."
		);
	}
} else if (typeof config.serverDb === "object" && config.serverDb) {
	exp.main = {
		...makeKnexConfig(config.serverDb),
	};
}

if (config.db.development) {
	exp.development = {
		...makeKnexConfig(config.db.development),
		seeds: {
			extension: "ts",
		},
	};
}
if (config.db.test) {
	exp.test = {
		...makeKnexConfig(config.db.test),
		asyncStackTraces: true,
	};
}
if (config.db.testserver) {
	exp.testserver = {
		...makeKnexConfig(config.db.testserver),
	};
}
if (config.db.staging) {
	exp.staging = {
		...makeKnexConfig(config.db.staging),
	};
}
if (config.db.production) {
	exp.production = {
		...makeKnexConfig(config.db.production),
	};
}
module.exports = exp;
