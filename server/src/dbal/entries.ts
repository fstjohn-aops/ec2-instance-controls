import _ from "lodash";
import {Knex} from "knex";
import {EntriesRow, EntriesSelect} from "../DbTypes";

export type EntriesWhere = Pick<EntriesRow, "id">;

/**
 * Gets all entries from the database.
 * @param {Knex} knex
 * @returns {Promise<EntriesSelect[]>}
 */
export async function getEntries(knex: Knex): Promise<EntriesSelect[]> {
	const entries = await knex("entries").select("*");
	return entries;
}
