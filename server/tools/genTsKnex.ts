import run from "./util/Run";
import Yargs from "yargs";
import {hideBin} from "yargs/helpers";

import Bluebird from "bluebird";
import _ from "lodash";
import * as FS from "fs";
import * as Path from "path";
import {makeKnex} from "./util/Knex";
import {replaceBody} from "./util/StringSplice";
import {runPrettier} from "./util/Prettier";
import {diffStrings} from "./util/Diff";

const RUN_PRETTIER = true;

const PROJECT_ROOT = Path.join(__dirname, "..");

// Tables that must exist for the script to run. Used to help warn users of
// messed up databases/migrations.
const EXPECTED_TABLE_NAMES = ["entries"];

type Args = {
	check: boolean;
	diff: boolean;
	force: boolean;
	"knex-path": string;
	"typebox-path": string;
	"camelcaser-path": string;
};

async function main() {
	const argv: Args = await Yargs(hideBin(process.argv))
		.strictOptions()
		.help()
		.version(false)
		.usage(
			"Generates the main bodies of some database-typescript helper files."
		)
		.usage(
			"src/knex.d.ts: Type definitions that knex understands. " +
				"Mostly unused in favor of wrappers in src/dbal and " +
				"liberal use of any with knex."
		)
		.usage(
			"src/DbTypes.ts: Typebox values for each table and " +
				"several associated Typescript aliases."
		)
		.usage(
			"src/DbCamelCaser.ts: Helpers for changing " +
				"snake-cased table rows to camel-cased."
		)
		.option("check", {
			alias: "c",
			describe: "Don't make changes; log and exit based on if any are needed.",
			type: "boolean",
			default: false,
		})
		.option("diff", {
			describe: "Print line-based diff. Noop without --check.",
			type: "boolean",
			default: false,
		})
		.option("force", {
			describe:
				"By default, errors if key tables are not found. " +
				"With this on, it will ignore the error and keep going.",
			type: "boolean",
			default: false,
		})
		.option("knex-path", {
			describe:
				"Destination of declaration file contents used by knex. Pass 'x' to skip.",
			type: "string",
			default: Path.normalize(Path.join(__dirname, "..", "src", "knex.d.ts")),
		})
		.option("typebox-path", {
			describe: "Destination of Typebox helpers and aliases. Pass 'x' to skip.",
			type: "string",
			default: Path.normalize(Path.join(__dirname, "..", "src", "DbTypes.ts")),
		})
		.option("camelcaser-path", {
			describe: "Destination of the camel-caser utility. Pass 'x' to skip.",
			type: "string",
			default: Path.normalize(
				Path.join(__dirname, "..", "src", "DbCamelCaser.ts")
			),
		}).argv;

	function log(message: string) {
		process.stderr.write(message);
	}

	const knex = await makeKnex();
	const rawColumnList: ColumnInfo[] = await knex
		.select(
			"table_name",
			"column_name",
			"data_type",
			"column_default",
			"is_nullable",
			"udt_name"
		)
		.from("information_schema.columns")
		.where("table_schema", "public")
		.orderBy(["table_name", "ordinal_position", "column_name"]);

	if (!rawColumnList.length) {
		throw new Error("No tables exist. Check that all migrations have run.\n");
	}
	const tableNames = rawColumnList.map((t) => t.table_name);
	const areAllExpectedTablesPresent = EXPECTED_TABLE_NAMES.every((tableName) =>
		tableNames.includes(tableName)
	);
	if (!areAllExpectedTablesPresent && !argv.force) {
		process.stderr.write(
			"Warning: key tables do not exist. " +
				"To force this script, use --force when running this script. " +
				"Expected tables: " +
				EXPECTED_TABLE_NAMES.join(", ")
		);
		process.exitCode = 1;
		throw new Error();
	}

	const filesToProcess = [
		{
			name: "knex",
			path: argv["knex-path"],
			computeTs: writeAllKnexTs,
		},
		{
			name: "typebox",
			path: argv["typebox-path"],
			computeTs: writeAllTypeboxTs,
		},
		{
			name: "camelcaser",
			path: argv["camelcaser-path"],
			computeTs: writeAllCamelCaserTs,
		},
	];

	const n = filesToProcess.length;
	await Bluebird.mapSeries(filesToProcess, async (file, i) => {
		const filePath = file.path;
		if (!filePath || filePath === "x") {
			log("---\n");
			log(`Skipping ${file.name} step (${i + 1}/${n})\n`);
			return;
		}
		const allTs = file.computeTs(rawColumnList);
		const filePathRel = Path.relative(PROJECT_ROOT, filePath);
		log("---\n");
		log(`Processing ${filePathRel} (${i + 1}/${n})\n`);

		// Let this throw if the path is bad.
		const fileContent = FS.readFileSync(filePath, "utf8");
		let fileNewContent = replaceBody({
			src: fileContent,
			begin: "//@@ BEGIN TABLES",
			end: "//@@ END TABLES",
			newBody: allTs,
			throwIfNotFound: true,
		});

		if (RUN_PRETTIER) {
			fileNewContent = await runPrettier(filePath, fileNewContent);
		}

		if (fileContent === fileNewContent) {
			log(filePathRel + " OK\n");
		} else if (argv.check) {
			process.exitCode = 1;
			log(filePathRel + " check failed\n");
			if (argv.diff) {
				log(diffStrings(fileContent, fileNewContent));
			}
		} else {
			FS.writeFileSync(filePath, fileNewContent, "utf8");
			log(filePathRel + " updated\n");
		}
	});
}

/**
 * Common helpers and types.
 */

function shouldIncludeTable(tableName: string): boolean {
	return !tableName.startsWith("knex_migrations") && tableName !== "mock_now";
}

type ColumnInfo = {
	table_name: string;
	column_name: string;
	data_type: string;
	column_default: string | null;
	is_nullable: string;
	udt_name: string;
};

/**
 * Functions/data for writing knex.d.ts.
 */

// TODO: using any for Dates. Insertions should be able to accept strings or
// Dates while returns should always expect dates. No easy way to do that, and
// we're trying not to rely on knex's inference anyway.

const pgToTsTypeTable: Record<string, string> = {
	boolean: "boolean",

	integer: "number",
	smallint: "number",
	bigint: "number",
	real: "number",
	"double precision": "number",
	numeric: "string", // surprisingly

	"character varying": "string",
	text: "string",
	uuid: "string",
	inet: "string",

	date: "any",
	"timestamp with time zone": "any",

	json: "JsonValue",
	jsonb: "JsonValue",

	// ARRAY handled specially
};

// When data_type is ARRAY in postgres, udt_name is indexed into this table to
// get the element type.
const pgUdtToTsTypeTable: Record<string, string> = {
	_int4: "number",
	_text: "string",
	_numeric: "string",
	_timestamptz: "any",
	_jsonb: "JsonValue",
};

function writeAllKnexTs(fullColumnList: ColumnInfo[]): string {
	const columnsByTable = _.pickBy(
		_.groupBy(fullColumnList, "table_name"),
		(_cols, tableName) => shouldIncludeTable(tableName)
	);

	const tableNames = _.sortBy(_.keys(columnsByTable));
	const allTableTs = tableNames.map((tableName) =>
		writeOneTableKnexTs(columnsByTable[tableName]!, tableName)
	);
	const tableListTs = writeTableListKnexTs(tableNames);
	return allTableTs.concat([tableListTs]).join("\n\n");
}

function writeTableListKnexTs(tableNames: string[]): string {
	return (
		`interface Tables {\n` +
		tableNames
			.map((tableName) => `\t${tableName}: Table_${tableName};\n`)
			.join("") +
		`}`
	);
}

function writeOneTableKnexTs(columns: ColumnInfo[], tableName: string): string {
	const columnLines = columns.map((column) => writeOneColumnKnexTs(column));
	return (
		`interface Table_${tableName} {\n` +
		columnLines.map((line) => `\t${line}\n`).join("") +
		`}`
	);
}

function writeOneColumnKnexTs(column: ColumnInfo): string {
	let mainType: string;
	if (column.data_type === "ARRAY") {
		const udtTsType = pgUdtToTsTypeTable[column.udt_name];
		if (udtTsType) {
			mainType = `${udtTsType}[]`;
		} else {
			console.error(
				`WARNING: Unrecognized data_type ARRAY + udt_name ${column.udt_name}; using any`
			);
			mainType = `any[]`;
		}
	} else {
		const mainTsType = pgToTsTypeTable[column.data_type];
		if (mainTsType) {
			mainType = mainTsType;
		} else {
			console.error(
				`WARNING: Unrecognized data_type ${column.data_type}; using any`
			);
			mainType = `any`;
		}
	}
	const nullSuffix = column.is_nullable === "YES" ? " | null" : "";
	let columnName = column.column_name;
	if (!/^[a-zA-Z_$][a-zA-Z0-9_$]*$/.test(columnName)) {
		columnName = `"${columnName}"`;
	}
	return `${columnName}: ${mainType}${nullSuffix};`;
}

/**
 * Functions/data for writing DbTypes.ts
 */

const pgToTypeboxTable: Record<string, string> = {
	boolean: "Type.Boolean()",

	integer: "Type.Number()",
	smallint: "Type.Number()",
	bigint: "Type.Number()",
	real: "Type.Number()",
	"double precision": "Type.Number()",
	numeric: "Type.String()", // surprisingly

	"character varying": "Type.String()",
	text: "Type.String()",
	uuid: "uuidT",
	inet: "Type.String()",

	date: "dateT",
	"timestamp with time zone": "dateT",

	json: "jsonT",
	jsonb: "jsonT",

	// ARRAY handled specially
};

// When data_type is ARRAY in postgres, udt_name is indexed into this table to
// get the element type.
const pgUdtToTypeboxTable: Record<string, string> = {
	_int4: "Type.Number()",
	_text: "Type.String()",
	_numeric: "Type.String()",
	_timestamptz: "dateT",
	_jsonb: "jsonT",
};

function writeAllTypeboxTs(fullColumnList: ColumnInfo[]): string {
	const columnsByTable = _.pickBy(
		_.groupBy(fullColumnList, "table_name"),
		(_cols, tableName) => shouldIncludeTable(tableName)
	);

	const tableNames = _.sortBy(_.keys(columnsByTable));
	const allTableTs = tableNames.map((tableName) =>
		writeOneTableTypeboxTs(columnsByTable[tableName]!, tableName)
	);
	const tableListTs = writeTableListTypeboxTs(tableNames);
	return _.concat(allTableTs, [tableListTs]).join("\n\n");
}

function writeTableListTypeboxTs(tableNames: string[]): string {
	const ccTableNames = tableNames.map((tableName) => _.camelCase(tableName));

	const staticLines = ccTableNames.map((ccTableName) => {
		const uccTableName = _.upperFirst(ccTableName);
		return `export type ${uccTableName}Row = Static<typeof ${ccTableName}T>;\n`;
	});

	const selectHeader = "\n// Type aliases best for getting select results\n";
	const selectLines = ccTableNames.map((ccTableName) => {
		const uccTableName = _.upperFirst(ccTableName);
		return `export type ${uccTableName}Select = Required<${uccTableName}Row>;\n`;
	});

	const insertHeader = "\n// Type aliases best for inserting rows\n";
	const insertLines = ccTableNames.map((ccTableName) => {
		const uccTableName = _.upperFirst(ccTableName);
		return `export type ${uccTableName}Insert = ${uccTableName}Row;\n`;
	});

	const updateHeader = "\n// Type aliases best for updating rows\n";
	const updateLines = ccTableNames.map((ccTableName) => {
		const uccTableName = _.upperFirst(ccTableName);
		return `export type ${uccTableName}Update = Partial<${uccTableName}Row>;\n`;
	});

	return (
		staticLines.join("") +
		selectHeader +
		selectLines.join("") +
		insertHeader +
		insertLines.join("") +
		updateHeader +
		updateLines.join("")
	);
}

function writeOneTableTypeboxTs(
	columns: ColumnInfo[],
	tableName: string
): string {
	const ccTableName = _.camelCase(tableName);
	const columnLines = columns.map((column) => writeOneColumnTypeboxTs(column));
	return (
		`export const ${ccTableName}T = Type.Object({\n` +
		columnLines.map((line) => `\t${line}\n`).join("") +
		`});`
	);
}

function writeOneColumnTypeboxTs(
	column: ColumnInfo,
	makeRequired?: boolean
): string {
	let mainType: string;
	if (column.data_type === "ARRAY") {
		const udtTsType = pgUdtToTypeboxTable[column.udt_name];
		if (udtTsType) {
			mainType = `Type.Array(${udtTsType})`;
		} else {
			console.error(
				`WARNING: Unrecognized data_type ARRAY + udt_name ${column.udt_name}; using any`
			);
			mainType = `Type.Array(Type.Any())`;
		}
	} else {
		const mainTsType = pgToTypeboxTable[column.data_type];
		if (mainTsType) {
			mainType = mainTsType;
		} else {
			console.error(
				`WARNING: Unrecognized data_type ${column.data_type}; using any`
			);
			mainType = `Type.Any()`;
		}
	}

	let finalType: string = mainType;
	if (makeRequired) {
		if (column.is_nullable === "YES") {
			finalType = `Nullable(${finalType})`;
		} else if (column.column_default !== null) {
			finalType = `${finalType}`;
		}
	} else {
		if (column.is_nullable === "YES") {
			finalType = `Type.Optional(Nullable(${finalType}))`;
		} else if (column.column_default !== null) {
			finalType = `Type.Optional(${finalType})`;
		}
	}

	let columnName = column.column_name;
	if (!/^[a-zA-Z_$][a-zA-Z0-9_$]*$/.test(columnName)) {
		columnName = `"${columnName}"`;
	}
	return `${columnName}: ${finalType},`;
}

/**
 * Functions/data for writing DbCamelCaser.ts
 */

function writeAllCamelCaserTs(fullColumnList: ColumnInfo[]): string {
	const columnsByTable = _.pickBy(
		_.groupBy(fullColumnList, "table_name"),
		(_cols, tableName) => shouldIncludeTable(tableName)
	);
	const tableNames = _.sortBy(_.keys(columnsByTable));
	const uccTableNames = tableNames.map((n) => _.upperFirst(_.camelCase(n)));

	const importTs =
		`import {\n` +
		uccTableNames.map((n) => `\t${n}Select,\n`).join("") +
		`} from "./DbTypes";`;

	const allTableTs = tableNames
		.map((t) => writeOneTableCamelCaserTs(columnsByTable[t]!, t))
		.join("\n\n");

	const funcObjLines = tableNames.map(
		(t) => `${t}: camelCase${_.upperFirst(_.camelCase(t))},`
	);
	const funcObjTs =
		`export const camelCasers = {\n` +
		funcObjLines.map((line) => `\t${line}\n`).join("") +
		`};`;

	return _.concat(importTs, allTableTs, funcObjTs).join("\n\n");
}

function writeOneTableCamelCaserTs(
	columns: ColumnInfo[],
	tableName: string
): string {
	const ccTableName = _.camelCase(tableName);
	const uccTableName = _.upperFirst(ccTableName);
	const typeColumnLines = columns.map((column) => {
		const scColumnName = column.column_name;
		const ccColumnName = _.camelCase(scColumnName);
		const srcObjType = `${uccTableName}Select`;
		return `\t${ccColumnName}: ${srcObjType}["${scColumnName}"];`;
	});
	const typeTColumnLines = columns.map((column) => {
		const scColumnName = column.column_name;
		const ccColumn = _.cloneDeep(column);
		const ccColumnName = _.camelCase(scColumnName);
		ccColumn.column_name = ccColumnName;
		return writeOneColumnTypeboxTs(ccColumn);
	});
	const typeTSelectColumnLines = columns.map((column) => {
		const scColumnName = column.column_name;
		const ccColumn = _.cloneDeep(column);
		const ccColumnName = _.camelCase(scColumnName);
		ccColumn.column_name = ccColumnName;
		return writeOneColumnTypeboxTs(ccColumn, true);
	});
	const funcColumnLines = columns.map((column) => {
		const scColumnName = column.column_name;
		const ccColumnName = _.camelCase(scColumnName);
		return `${ccColumnName}: row.${scColumnName},`;
	});
	const funcColumnLinesPartial = columns.map((column) => {
		const scColumnName = column.column_name;
		const ccColumnName = _.camelCase(scColumnName);
		return `...("${scColumnName}" in row ? \{${ccColumnName}: row.${scColumnName}\} : {}),`;
	});
	const funcCcToScColumnLines = columns.map((column) => {
		const scColumnName = column.column_name;
		const ccColumnName = _.camelCase(scColumnName);
		return `...("${ccColumnName}" in row ? \{${scColumnName}: row.${ccColumnName}\} : {}),`;
	});
	return (
		`export type ${uccTableName}CamelCased = {\n` +
		typeColumnLines.map((line) => `\t${line}\n`).join("") +
		`};\n` +
		`\n` +
		`export const ${ccTableName}CamelCasedT = Type.Object({\n` +
		typeTColumnLines.map((line) => `\t${line}\n`).join("") +
		`})\n` +
		`\n` +
		`export const ${ccTableName}SelectCamelCasedT = Type.Object({\n` +
		typeTSelectColumnLines.map((line) => `\t${line}\n`).join("") +
		`})\n` +
		`\n` +
		`export function camelCase${uccTableName}(\n` +
		`\trow: ${uccTableName}Select\n` +
		`): ${uccTableName}CamelCased {\n` +
		`\treturn {` +
		funcColumnLines.map((line) => `\t\t${line}\n`).join("") +
		`\t};` +
		`}` +
		`export function camelCase${uccTableName}Partial(\n` +
		`\trow: Partial<${uccTableName}Select>\n` +
		`): Partial<${uccTableName}CamelCased> {\n` +
		`\treturn {` +
		funcColumnLinesPartial.map((line) => `\t\t${line}\n`).join("") +
		`\t};` +
		`}` +
		`export function snakeCase${uccTableName}Partial(\n` +
		`\trow: Partial<${uccTableName}CamelCased>\n` +
		`): Partial<${uccTableName}Select> {\n` +
		`\treturn {` +
		funcCcToScColumnLines.map((line) => `\t\t${line}\n`).join("") +
		`\t};` +
		`}`
	);
}

/**
 * Script startup.
 */

run(main);
