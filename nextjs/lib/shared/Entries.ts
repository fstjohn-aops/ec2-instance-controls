//@@ BEGIN CODEGEN WARNING
/**
 * NOTE: CODEGEN IS USED IN THIS FILE. Careless manual edits may be lost.
 *
 * server/tools/syncDirs.ts keeps this file in sync with:
 *   server/src/shared/Entries.ts
 *
 * You can run it with the following command:
 * 	npm run gen-sync-shared
 */
//@@ END CODEGEN WARNING

import {Type} from "@sinclair/typebox";
import {Nullable, dateT} from "@aops-trove/fast-server-common";

export const entriesResponseT = Type.Object({
	entries: Type.Array(
		Type.Object({
			id: Type.String({format: "uuid"}),
			entry: Type.String(),
			createdAt: Type.Optional(dateT),
			updatedAt: Type.Optional(dateT),
			deletedAt: Type.Optional(Nullable(Type.String())),
		})
	),
});
