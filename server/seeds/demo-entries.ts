import type {Knex} from "knex";

export const seed = async function (knex: Knex) {
	// Deletes ALL existing entries
	await knex("entries").del();
	await knex("entries").insert([
		{
			id: "4b0b869b-a596-481e-8255-ccbc8b9a525a",
			entry: "Hello, world",
			created_at: "2024-02-12 00:55:10.654881+00",
			updated_at: "2024-02-12 00:55:10.654881+00",
			deleted_at: null,
		},
	]);
};
