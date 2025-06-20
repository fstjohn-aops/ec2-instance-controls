/**
 * File that sets up the Postgres database connection using knex.
 *
 * This file is also used by tools/, so take care with new imports.
 */

import {Knex, knex as knexFactory} from "knex";
import {ProjectConfig, ProjectDbConfig} from "./ProjectConfig";

export async function initKnex(projectConfig: ProjectConfig): Promise<Knex> {
	// This could be a string key into projectConfig.db or the connection info.
	// Takes some juggling to resolve it in a way that Typescript likes.
	const valueFromConfig = projectConfig.serverDb || "development";

	let dbConfig: ProjectDbConfig | undefined;
	if (typeof valueFromConfig === "string") {
		dbConfig = projectConfig.db[valueFromConfig];
	} else {
		dbConfig = valueFromConfig;
	}
	if (!dbConfig) {
		throw new Error("config.yaml serverDb could not be resolved");
	}

	const knexConfig: Knex.Config = {
		client: "pg",
		connection: {
			host: dbConfig.host,
			port: dbConfig.port || 5432,
			database: dbConfig.dbname,
			user: dbConfig.user,
			password: dbConfig.password,
		},
		pool: {
			min: dbConfig.poolMin || 1,
			max: dbConfig.poolMax || 1,
		},
	};

	const knex: Knex = knexFactory(knexConfig);
	return knex;
}
