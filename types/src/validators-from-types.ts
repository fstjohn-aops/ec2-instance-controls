/**
 * NOTE: CODEGEN IS USED IN THIS FILE. Careless manual edits may be lost.
 *
 * generate-validators.ts keeps this file in sync with:
 *   src/types.ts
 *
 * Run with the following command:
 *   npm run generate
 */
import {Type, Static} from "@sinclair/typebox";

export type exampleRequestT = Static<typeof exampleRequestT>;
export const exampleRequestT = Type.Object({
	id: Type.Readonly(Type.String()),
	version: Type.Readonly(Type.String()),
	getNext: Type.ReadonlyOptional(Type.Boolean()),
});
