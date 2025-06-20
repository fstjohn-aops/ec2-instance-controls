/**
 * NOTE: CODEGEN IS USED IN THIS FILE. Careless manual edits may be lost.
 *
 * This file provides types for the database tables and columns so that
 * Typescript can help out with knex queries.
 *
 * Run `npx tsx tools/genTsKnex.ts` to update the codegen'd portion.
 * Everything between @@ BEGIN TABLES and @@ END TABLES is controlled by this
 * script, and the original body is discarded.
 */

// Needed to merge declarations instead of override.
import "knex";
import {JsonValue} from "@aops-trove/fast-server-common";

declare module "knex/types/tables" {
	//@@ BEGIN TABLES
	interface Table_entries {
		id: string;
		entry: string;
		created_at: any;
		updated_at: any;
		deleted_at: string | null;
	}

	interface Tables {
		entries: Table_entries;
	}

	//@@ END TABLES
}
