/**
 * File that loads and parses the config YAML file. See README_config for more
 * information.
 */

import "dotenv/config";
import _ from "lodash";
import * as Path from "path";
import {processEnv} from "@aops-trove/fast-server-common";
import {IS_DEV, IS_DOCKER, SERVER_ROOT, loadYAMLSync} from "../util/General";

export type ProjectDbConfig = {
	host: string;
	port?: number;
	dbname: string;
	user: string;
	password: string;
	poolMin?: number;
	poolMax?: number;
};

export type ProjectConfig = {
	dev: {
		// All keys here need to be optional so production can replace it with {}.
		allowDevLogin?: boolean;
		alwaysResetCrons?: boolean;
		disableCrons?: boolean;
	};

	db: {[key: string]: ProjectDbConfig};

	serverDb: string | ProjectDbConfig;

	host: string;
	port: number;
	baseUrl: string;

	alsoWorker?: boolean;

	apiKey?: string;

	redisHost?: string;
	redisPort?: number;
	redisDb?: number;
	redisPassword?: string;

	cookieSignatureKey: string;
	cookieSignatureKeyOld: string;
	applicationCode: string;

	platform: {
		url: string;
		loginDomain: string;
		apiKey: string;
	};

	aops: {
		url: string;
		api: {
			key: string;
			email: string;
		};
		htaccess: {
			user: string;
			password: string;
		};
	};
};

export function initProjectConfig(): ProjectConfig {
	const mainConfigPath = getMainConfigPath();
	if (!mainConfigPath) {
		throw new Error(
			"SERVER_CONFIG_PATH was not specified. " +
				"See README_config.md for info."
		);
	}

	let projectConfig: ProjectConfig = loadYAMLSync(
		Path.join(SERVER_ROOT, mainConfigPath)
	);

	try {
		const overridesConfig: any = loadYAMLSync(
			Path.join(SERVER_ROOT, "config.override.yaml")
		);
		_.merge(projectConfig, overridesConfig);
	} catch (ex: any) {
		if (ex.code === "ENOENT") {
			// Ignore; okay to have no overrides file
		} else {
			throw ex;
		}
	}

	if (!IS_DEV) {
		// Do not allow any dev flags in production.
		projectConfig.dev = {};
	}

	projectConfig = processEnv(projectConfig);
	return projectConfig;
}

function getMainConfigPath(): string | undefined {
	if (IS_DOCKER) {
		return process.env.SERVER_CONFIG_PATH;
	} else {
		return (
			process.env.SERVER_NONDOCKER_CONFIG_PATH || process.env.SERVER_CONFIG_PATH
		);
	}
}
