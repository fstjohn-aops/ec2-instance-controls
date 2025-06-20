import {Knex} from "knex";

export async function up(knex: Knex): Promise<void> {
	await knex.schema.createTable("entries", function (table) {
		table.comment("Example table");
		table.uuid("id").notNullable().unique().primary();
		table.string("entry").notNullable();
		table.timestamp("created_at").defaultTo(knex.raw("now()")).notNullable();
		table.timestamp("updated_at").defaultTo(knex.raw("now()")).notNullable();
		table.string("deleted_at");
	});
}

export async function down(knex: Knex): Promise<void> {
	return knex.schema.dropTable("entries");
}
