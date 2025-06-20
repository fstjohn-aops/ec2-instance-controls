/**
 * NOTE: CODEGEN IS USED IN THIS FILE. Careless manual edits may be lost.
 *
 * This file provides camel-casing helpers for the database row types. Pass
 * a row from the database with snake-cased keys to the appropriate function,
 * and you will get back a row with camel-cased keys. All columns will be set,
 * possibly with value undefined.
 *
 * Run `npx tsx tools/genTsKnex.ts` to update the codegen'd portion.
 * Everything between @@ BEGIN TABLES and @@ END TABLES is controlled by this
 * script, and the original body is discarded.
 */

import {Type} from "@sinclair/typebox";
import {Nullable, dateT} from "@aops-trove/fast-server-common";
const uuidT = Type.String({format: "uuid"});

//@@ BEGIN TABLES
import {EntriesSelect} from "./DbTypes";

export type EntriesCamelCased = {
	id: EntriesSelect["id"];
	entry: EntriesSelect["entry"];
	createdAt: EntriesSelect["created_at"];
	updatedAt: EntriesSelect["updated_at"];
	deletedAt: EntriesSelect["deleted_at"];
};

export const entriesCamelCasedT = Type.Object({
	id: uuidT,
	entry: Type.String(),
	createdAt: Type.Optional(dateT),
	updatedAt: Type.Optional(dateT),
	deletedAt: Type.Optional(Nullable(Type.String())),
});

export const entriesSelectCamelCasedT = Type.Object({
	id: uuidT,
	entry: Type.String(),
	createdAt: dateT,
	updatedAt: dateT,
	deletedAt: Nullable(Type.String()),
});

export function camelCaseEntries(row: EntriesSelect): EntriesCamelCased {
	return {
		id: row.id,
		entry: row.entry,
		createdAt: row.created_at,
		updatedAt: row.updated_at,
		deletedAt: row.deleted_at,
	};
}
export function camelCaseEntriesPartial(
	row: Partial<EntriesSelect>
): Partial<EntriesCamelCased> {
	return {
		...("id" in row ? {id: row.id} : {}),
		...("entry" in row ? {entry: row.entry} : {}),
		...("created_at" in row ? {createdAt: row.created_at} : {}),
		...("updated_at" in row ? {updatedAt: row.updated_at} : {}),
		...("deleted_at" in row ? {deletedAt: row.deleted_at} : {}),
	};
}
export function snakeCaseEntriesPartial(
	row: Partial<EntriesCamelCased>
): Partial<EntriesSelect> {
	return {
		...("id" in row ? {id: row.id} : {}),
		...("entry" in row ? {entry: row.entry} : {}),
		...("createdAt" in row ? {created_at: row.createdAt} : {}),
		...("updatedAt" in row ? {updated_at: row.updatedAt} : {}),
		...("deletedAt" in row ? {deleted_at: row.deletedAt} : {}),
	};
}

export const camelCasers = {
	entries: camelCaseEntries,
};

//@@ END TABLES
