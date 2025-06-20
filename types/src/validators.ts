// Use this file to export handwritten TypeBox objects.

// In most cases, one would write a TypeScript type in src/types.ts. All types defined
// in that file are codegen'd into exported TypeBox objects.
import {Static, Type} from "@sinclair/typebox";
import {Nullable, dateT} from "@aops-trove/fast-server-common";

export type entriesResponseT = Static<typeof entriesResponseT>;
export const entriesResponseT = Type.Object({
	entries: Type.Array(
		Type.Object({
			id: Type.String({format: "uuid"}),
			version: Type.String(),
			created_at: Type.Optional(dateT),
			updated_at: Type.Optional(dateT),
			deleted_at: Type.Optional(Nullable(dateT)),
		})
	),
});
