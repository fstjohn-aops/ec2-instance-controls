import {entriesResponseT} from "../src/validators";

const exampleResponse: entriesResponseT = {
	entries: [
		{
			id: "1",
			version: "v1",
		},
		{
			id: "2",
			version: "v1",
			created_at: new Date(),
		},
		{
			id: "3",
			version: "v2",
			updated_at: new Date(),
		},
		{
			id: "4",
			version: "v1",
			deleted_at: new Date(),
		},
	],
};

// Test published schemas to keep behavior consistent across changes
describe("Ensure API response", () => {
	test("has entries", () => {
		expect(exampleResponse).toHaveProperty("entries");
		expect(Array.isArray(exampleResponse.entries));
	});

	test("has entries with defined id and version", () => {
		exampleResponse.entries.forEach((entry) => {
			expect(entry.id).toBeDefined();
			expect(entry.version).toBeDefined();
		});
	});

	test("has entries with optional created_at, deleted_at, updated_at", () => {
		let hasEntryWithCreated = false;
		let hasEntryWithUpdated = false;
		let hasEntryWithDeleted = false;

		exampleResponse.entries.forEach((entry) => {
			if (entry.created_at) {
				hasEntryWithCreated = true;
			}

			if (entry.updated_at) {
				hasEntryWithUpdated = true;
			}
			if (entry.deleted_at) {
				hasEntryWithDeleted = true;
			}
		});

		expect(hasEntryWithCreated).toBe(true);
		expect(hasEntryWithUpdated).toBe(true);
		expect(hasEntryWithDeleted).toBe(true);
	});
});
