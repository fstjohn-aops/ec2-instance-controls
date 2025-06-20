import {Type} from "@sinclair/typebox";
import {exampleRequestT} from "../src/validators-from-types";
import {checkTypebox} from "@aops-trove/fast-server-common";
const exampleObject: exampleRequestT = {
	id: "abc",
	version: "123",
};

const anotherExampleObject: exampleRequestT = {
	id: "abc",
	version: "123",
	getNext: true,
};

const exampleNotPassingValidation = {
	id: "abc",
};

// Test that at least one of the generated schemas matches the intended type
// If you have no generated schemas, test.skip() or delete the test
describe("TypeBox code generation", () => {
	test("Generated TypeBox schema matches TypeScript type", () => {
		const expectedSchema = Type.Object({
			id: Type.Readonly(Type.String()),
			version: Type.Readonly(Type.String()),
			getNext: Type.ReadonlyOptional(Type.Boolean()),
		});

		// Compare the generated schema with the expected schema
		expect(exampleRequestT).toEqual(expectedSchema);

		checkTypebox({schema: exampleRequestT, value: exampleObject});
		checkTypebox({schema: exampleRequestT, value: anotherExampleObject});

		expect(() =>
			checkTypebox({
				schema: exampleRequestT,
				value: exampleNotPassingValidation,
			})
		).toThrow();
	});
});
