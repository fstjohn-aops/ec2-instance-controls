/**
 * Utility to set up a database connection suitable for use in scripts.
 * Also sets up the necessary cleanup.
 */

import _ from "lodash";
import {Knex, knex as knexFactory} from "knex";
import {ProjectDbConfig, initProjectConfig} from "../../src/init/ProjectConfig";
import {initKnex} from "../../src/init/Knex";
import {registerCleanupFunction} from "./Run";

type MakeKnexArg = null | string | ProjectDbConfig | Knex.Config;

/**
 * Create a knex connection. The argument can customize what it connects to.
 * Possible forms are:
 * - string: Provide a key in config.yaml's db map. Use it to connect.
 * - object, config.yaml form: Provide an object structured similarly to how
 *   config.yaml structures db config.
 * - object, knex form: Provide an argument you would pass to knex when
 *   constructing it.
 *
 * If you use the run util, there is no need to call destroy on the returned
 * knex instance. A cleanup function will be registered for you.
 */
export async function makeKnex(arg: MakeKnexArg = null): Promise<Knex> {
	let knex: Knex;
	if (_.isObject(arg) && "client" in arg) {
		knex = knexFactory(arg);
	} else {
		let projectConfig = initProjectConfig();
		if (arg !== null) {
			projectConfig = _.extend({}, projectConfig, {serverDB: arg});
		}
		try {
			knex = await initKnex(projectConfig);
		} catch (ex: any) {
			if (ex.message.startsWith("config.yaml serverDB")) {
				const key = projectConfig.serverDb || "development";
				throw new Error("config.yaml had no db key " + key);
			}
			throw ex;
		}
	}
	registerCleanupFunction(() => knex.destroy());
	return knex;
}
