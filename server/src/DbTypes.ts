/**
 * NOTE: CODEGEN IS USED IN THIS FILE. Careless manual edits may be lost.
 *
 * This file provides typebox definitions for the database tables. Import them
 * or their static versions to help with writing database code.
 *
 * Run `npx tsx tools/genTsKnex.ts` to update the codegen'd portion.
 * Everything between @@ BEGIN TABLES and @@ END TABLES is controlled by this
 * script, and the original body is discarded.
 */

import {Static, Type} from "@sinclair/typebox";
import {Nullable, dateT} from "@aops-trove/fast-server-common";
const uuidT = Type.String({format: "uuid"});

//@@ BEGIN TABLES
export const entriesT = Type.Object({
	id: uuidT,
	entry: Type.String(),
	created_at: Type.Optional(dateT),
	updated_at: Type.Optional(dateT),
	deleted_at: Type.Optional(Nullable(Type.String())),
});

export type EntriesRow = Static<typeof entriesT>;

// Type aliases best for getting select results
export type EntriesSelect = Required<EntriesRow>;

// Type aliases best for inserting rows
export type EntriesInsert = EntriesRow;

// Type aliases best for updating rows
export type EntriesUpdate = Partial<EntriesRow>;

//@@ END TABLES
