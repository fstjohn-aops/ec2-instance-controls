import {Knex} from "./MockKnex";

export async function insertTestRow(knex: Knex, table: string, row: any) {
	await knex(table).insert(row);
}

export async function insertTestRows(knex: Knex, table: string, rows: any[]) {
	await Promise.all(rows.map((r) => insertTestRow(knex, table, r)));
}

/**
 * Tiny utility that wraps a promise. Use in tests where you expect a Promise
 * to reject.
 *
 * If the passed promise fulfills, this returns one that rejects. If the passed
 * promise rejects, this returns one that fulfills with the error. The optional
 * second argument can be used to add a bit more info to the error in the
 * possibly-rejected promise.
 */
export function expectError(p: Promise<any>, callType = ""): Promise<any> {
	const suffix = callType ? " by " + callType : "";
	return p.then(
		() => {
			throw new Error("Expected error to be thrown" + suffix);
		},
		(e) => e
	);
}
