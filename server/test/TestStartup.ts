/**
 * This file is run at test startup using Jest's globalSetup hook.
 * Note we do not import MockKnex here to avoid running its hooks.
 */

import {Knex as KnexType} from "knex";
// @ts-ignore (let this be imported as any)
import Knexfile from "../knexfile";
import {type Config as JestConfig} from "@jest/types";
import {
	KnexConfigWithObjConn,
	createTestDbFleet,
	TimeWarp,
} from "@aops-trove/fast-test-db";

export default async function (globalConfig: JestConfig.GlobalConfig) {
	await createTestDbFleet({
		knexConfig: Knexfile.test as KnexConfigWithObjConn,
		baseName: "fastackstarter_test",
		count: globalConfig.maxWorkers,
		preMigrateHook,
	});
}

/**
 * Perform database setup steps that mimic the initialization of the Docker
 * database containers.
 */
async function preMigrateHook(knex: KnexType) {
	await TimeWarp.setupDbForTimeWarp(knex);
}
