import run from "./util/Run";
import Yargs from "yargs";
import {hideBin} from "yargs/helpers";

import Bluebird from "bluebird";
import _ from "lodash";
import * as FS from "fs";
import * as Path from "path";
import {sync} from "glob";
import {findCodegenConfig} from "./util/CodegenConfig";
import {grep} from "./util/Grep";
import {replaceBody} from "./util/StringSplice";
import {runPrettier} from "./util/Prettier";
import {diffStrings} from "./util/Diff";

const RUN_PRETTIER = true;

const SERVER_ROOT = Path.join(__dirname, "..");
const SRC_DIR = Path.join(SERVER_ROOT, "src");

const BEGIN_DELIM = "//@@ BEGIN BULKIMPORT";
const END_DELIM = "//@@ END BULKIMPORT";

type Args = {
	check: boolean;
	diff: boolean;
};

async function main() {
	const argv: Args = await Yargs(hideBin(process.argv))
		.strictOptions()
		.help()
		.version(false)
		.usage(
			"Finds bulk import codegen blocks, marked by //@@ BEGIN BULKIMPORT, " +
				"and rewrites their bodies to account for all pointed-to files."
		)
		.usage(
			"Above the //@@ BEGIN BULKIMPORT line, configure the bulk import with " +
				"lines of the form //@@ var = value."
		)
		.usage(
			"Available variables:\n" +
				"- dir: required; the directories (comma-separated) to bulk import\n" +
				"- exclude: comma separated list of globs; matches are skipped\n" +
				"- type: the expected TypescriptType of every file's export (default any)\n" +
				"- varName: required; the variable name that holds the results\n"
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
		}).argv;

	const filesToProcess = await grep(SRC_DIR, BEGIN_DELIM);
	console.log(
		`Found ${filesToProcess.length} file(s) with bulk import markers`
	);
	await Bluebird.mapSeries(filesToProcess, async (p) => {
		console.log(`Processing ${p}...`);
		await processFile(argv, p);
	});
	console.log(`Done`);
}

async function processFile(argv: Args, filePath: string) {
	const fileContent = FS.readFileSync(filePath, "utf8");
	const filePathRel = Path.relative(SERVER_ROOT, filePath);

	const config = findCodegenConfig({
		src: fileContent,
		begin: BEGIN_DELIM,
	});

	if (!config) {
		throw new Error(
			`Valid begin delimiter (${BEGIN_DELIM}) not found in ${filePath}`
		);
	} else if (!config.dir) {
		throw new Error(`Codegen config did not set 'dir' in ${filePath}`);
	} else if (!config.varName) {
		throw new Error(`Codegen config did not set 'varName' in ${filePath}`);
	}

	const exclude = (config.exclude || "")
		.split(", ")
		.map((s) => s.trim())
		.filter(Boolean)
		.map((s) => (s.includes("**") ? s : Path.join("**", s)));
	const importType = config.type || "any";

	const dirs = config.dir.split(",").map((s) => s.trim());

	const toBulkImportAbs = _.flatMap(dirs, (dir) => {
		const search = Path.join(SERVER_ROOT, dir, "**", "*.ts");
		return sync(search, {
			ignore: exclude,
		});
	});

	function stripTs(s: string): string {
		return s.endsWith(".ts") ? s.slice(0, -3) : s;
	}

	const importNames = toBulkImportAbs.map((absP) => {
		const relP = Path.relative(SERVER_ROOT, absP);
		const importNameParts = stripTs(relP).split(/[^a-zA-Z0-9_]/g);
		const importName = importNameParts.map((s) => _.upperFirst(s)).join("_");
		return importName;
	});

	const importTs = toBulkImportAbs
		.map((absP, i) => {
			const importName = importNames[i];
			let importPath = stripTs(Path.relative(Path.dirname(filePath), absP));
			if (!importPath.startsWith(".")) {
				importPath = "." + Path.sep + importPath;
			}
			return `import ${importName} from "${importPath}"`;
		})
		.join("\n");

	const varTsBegin = `const ${config.varName}: ${importType}[] = [\n`;
	const varTsEnd = `];\n`;
	const varTsBody = toBulkImportAbs
		.map((_absP, i) => {
			const importName = importNames[i];
			return `\t${importName},`;
		})
		.join("\n");
	const varTs = varTsBegin + varTsBody + varTsEnd;

	const allTs = importTs + "\n\n" + varTs;

	let fileNewContent = replaceBody({
		src: fileContent,
		begin: BEGIN_DELIM,
		end: END_DELIM,
		newBody: allTs,
		throwIfNotFound: true,
	});

	if (RUN_PRETTIER) {
		fileNewContent = await runPrettier(filePath, fileNewContent);
	}

	if (fileContent === fileNewContent) {
		console.log(filePathRel + " OK");
	} else if (argv.check) {
		process.exitCode = 1;
		console.log(filePathRel + " check failed");
		if (argv.diff) {
			console.log(diffStrings(fileContent, fileNewContent));
		}
	} else {
		FS.writeFileSync(filePath, fileNewContent, "utf8");
		console.log(filePathRel + " updated");
	}
}

/**
 * Script startup.
 */

run(main);
