import _ from "lodash";
import {Knex} from "knex";

export type PropsWithKnex<T> = T & {knex: Knex};

/**
 * Utils for building new tables.
 */
export function addTimestampColumns({
	table,
	knex,
}: PropsWithKnex<{table: Knex.CreateTableBuilder}>) {
	table.timestamp("created_at").notNullable().defaultTo(knex.raw("now()"));
	table.uuid("created_by").notNullable();
	table.timestamp("updated_at").notNullable().defaultTo(knex.raw("now()"));
	table.uuid("updated_by").notNullable();
	table.timestamp("deleted_at");
	table.uuid("deleted_by");
}

export type TableConstructor = (tableBuilder: Knex.CreateTableBuilder) => void;
function newTable({
	constructor,
	knex,
}: PropsWithKnex<{constructor: TableConstructor}>): TableConstructor {
	return (table) => {
		constructor(table);
		addTimestampColumns({table, knex});
	};
}

type NewTables = {[tableName: string]: TableConstructor};
// TODO: Make addition of timestamps optional.
export function newTablesUp({
	newTables,
	knex,
}: PropsWithKnex<{newTables: NewTables}>): Knex.SchemaBuilder {
	return Object.keys(newTables).reduce(
		(schema, table) =>
			schema.createTable(
				table,
				newTable({
					knex: knex,
					constructor: newTables[table]!,
				})
			),
		knex.schema
	);
}

export function newTablesDown({
	tableNames,
	knex,
}: PropsWithKnex<{tableNames: readonly string[]}>): Knex.SchemaBuilder {
	return tableNames.reduce(
		(schema, table) => schema.dropTableIfExists(table),
		knex.schema
	);
}

/**
 * Utils for running queries.
 */

/**
 * Insert new rows into a table and return the inserted rows.
 * Copied from grid-crypt.
 * @TODO: extract to fast-postgres
 */
export async function insertRows<T>({
	table,
	insert,
	knex,
}: PropsWithKnex<{
	table: string;
	insert: Partial<T>[];
}>): Promise<T[]> {
	const query = knex(table).insert(insert).returning("*");
	return ((await query) || []) as T[];
}

/**
 * Select rows from a table.
 * Copied from grid-crypt.
 * @TODO: Extract to fast-postgres
 */
export async function selectRows<T>({
	table,
	modifyKnex,
	where,
	knex,
}: PropsWithKnex<{
	table: string;
	modifyKnex?: (query: Knex.QueryBuilder) => void;
	where: Partial<T>;
}>): Promise<T[]> {
	const query = knex(knex.ref(table).as("i")).select("i.*");

	query.where(_.mapKeys(where, (_v, k) => `i.${k}`));

	if (modifyKnex) {
		modifyKnex(query);
	}

	return ((await query) || []) as T[];
}
