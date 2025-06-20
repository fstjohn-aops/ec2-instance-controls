import {Knex as KnexType} from "knex";
// @ts-ignore (let this be imported as any)
import Knexfile from "../knexfile";
import {
	KnexConfigWithObjConn,
	registerMockKnexDb,
	setupMockKnexJestHooks,
	makeMockKnex as baseMakeMockKnex,
} from "@aops-trove/fast-test-db";

// Re-export for convenience
export {KnexType as Knex};

type DbName = "fastackstarter";

registerMockKnexDb("fastackstarter", {
	knexConfig: Knexfile.test as KnexConfigWithObjConn,
	fleetBaseName: "fastackstarter_test",
});
setupMockKnexJestHooks();

export async function makeMockKnex(name: DbName = "fastackstarter") {
	return baseMakeMockKnex(name);
}
