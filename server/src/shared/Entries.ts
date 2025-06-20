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
