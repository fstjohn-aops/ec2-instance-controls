import run from "./util/Run";
import Yargs from "yargs";
import {hideBin} from "yargs/helpers";
import * as Path from "path";
import {globSync} from "glob";
import * as Fs from "fs/promises";
import Bluebird from "bluebird";
import mkdirp from "mkdirp";
import {Type, Static} from "@sinclair/typebox";
import {checkTypebox} from "@aops-trove/fast-server-common";
import {replaceBody} from "./util/StringSplice";

type Args = {
	src?: string;
	dest?: string;
	exclude?: (string | number)[];
	"codegen-banner"?: boolean;
	root?: string;
	json?: string;
	check?: boolean;
};

const jsonInputT = Type.Object({
	src: Type.String(),
	dest: Type.String(),
	exclude: Type.Optional(Type.Array(Type.String())),
	codegenBanner: Type.Optional(Type.Boolean()),
	root: Type.Optional(Type.String()),
});
type JsonInput = Static<typeof jsonInputT>;

async function main() {
	const argv: Args = await Yargs(hideBin(process.argv))
		.strictOptions()
		.help()
		.version(false)
		.usage(
			"Copy the contents of one directory to another " +
				"so that both have the same contents."
		)
		.usage("Extra files in the destination will be deleted.")
		.usage(
			"Used for having shared files in client and server " +
				"without forcing Typescript to import outside its root."
		)
		.option("src", {
			describe: "Required source directory.",
			type: "string",
		})
		.option("dest", {
			describe: "Required destination directory.",
			type: "string",
		})
		.option("exclude", {
			describe: "Globs to not consider when syncing.",
			type: "array",
		})
		.option("root", {
			describe:
				"Optional path to project root. " +
				"Used for generating the text in the codegen banner. " +
				"As --root, relative to cwd. In JSON, relative to JSON's path.",
			type: "string",
		})
		.option("json", {
			describe:
				"Path to JSON describing syncs to perform. " +
				"" +
				"JSON should be an object or array of objects with keys " +
				"src (string), dest (string), exclude (opt string array), " +
				"codegenBanner (opt boolean), root (opt string). " +
				"If set, all options but --check will be ignored.",
			type: "string",
		})
		.option("check", {
			describe:
				"Do not update or remove files; " +
				"only check if they are as expected. " +
				"Logs and exits nonzero if any issues found.",
			type: "boolean",
		})
		.option("codegen-banner", {
			describe:
				"If true, add commented text at the top of the file " +
				"indicating it is produced by codegen.",
			type: "boolean",
		}).argv;

	const {src, dest, json, check = false} = argv;
	let inputs: JsonInput[] = [];
	if (!json) {
		if (!src) {
			throw new Error("--src is required");
		} else if (!dest) {
			throw new Error("--dest is required");
		}
		const resolvedRoot = Path.resolve(process.cwd(), argv.root || "");
		inputs = [
			{
				src,
				dest,
				exclude: (argv.exclude || [])
					.map((x) => (typeof x === "number" ? "" : x))
					.filter(Boolean),
				codegenBanner: !!argv["codegen-banner"],
				root: resolvedRoot,
			},
		];
	} else {
		if (src || dest || argv.exclude || argv["codegen-banner"] || argv.root) {
			console.warn(
				"WARNING: Ignoring src, dest, exclude, codegen-banner, and root " +
					"options because --json was set."
			);
		}

		const jsonConfigSrc = await Fs.readFile(json, "utf8");
		const jsonConfigParsed = JSON.parse(jsonConfigSrc);
		const jsonConfigArr = Array.isArray(jsonConfigParsed)
			? jsonConfigParsed
			: [jsonConfigParsed];

		console.log(
			`Found json config in ${json} with ${jsonConfigArr.length} entries, verifying shape...`
		);
		inputs = jsonConfigArr.map((untyped: unknown) => {
			const checked = checkTypebox({
				schema: jsonInputT,
				value: untyped,
			});

			return checked;
		});
		inputs = inputs.map((input: JsonInput) => {
			return {
				...input,
				root: Path.resolve(Path.dirname(json), input.root || ""),
			};
		});
	}

	const verb = check ? "Checking" : "Syncing";
	const allActionRes = await Bluebird.mapSeries(inputs, async (input) => {
		console.log(`${verb} ${input.src} to ${input.dest}...`);
		const res = await processInput(input, check);
		return res;
	});

	const allOk = allActionRes.every((x) => x);
	if (check && !allOk) {
		console.log("Check found differences");
		process.exitCode = 1;
	} else if (check) {
		console.log("OK");
	} else {
		console.log("Done");
	}
}

// Returns whether the check succeeded.
async function processInput(
	input: JsonInput,
	check: boolean
): Promise<boolean> {
	const {src, dest, root} = input;
	const banner = !!input.codegenBanner;
	// An exclude argument of "README.md" should become the glob "**/README.md",
	// like in gitignore.
	const realExclude = (input.exclude || []).map((p) =>
		p.startsWith("*") || p.startsWith(Path.sep) ? p : Path.join("**", p)
	);

	let checkError = false;

	const srcGlob = Path.join(src, "**");
	const destGlob = Path.join(dest, "**");

	const srcFiles = globSync(srcGlob, {
		ignore: realExclude.map((p) => Path.join(src, p)),
		nodir: true,
	});
	const destFiles = globSync(destGlob, {
		ignore: realExclude.map((p) => Path.join(dest, p)),
		nodir: true,
	});

	const srcRelPaths = srcFiles.map((p) => Path.relative(src, p));
	const srcRelSet = new Set(srcRelPaths);

	if (check) {
		console.log(`  Checking for stray files in ${dest}...`);
	} else {
		console.log(`  Removing stray files from ${dest}...`);
	}
	await Bluebird.mapSeries(destFiles, async (destP) => {
		if (!srcRelSet.has(Path.relative(dest, destP))) {
			if (check) {
				console.log(
					`  CHECK FAILED: ${destP} is not in ${src} and should be removed`
				);
				checkError = true;
			} else {
				console.log(`  Removing ${destP}...`);
				await Fs.unlink(destP);
			}
		}
	});

	if (check) {
		console.log(`  Checking files match between ${src} and ${dest}...`);
	} else {
		console.log(`  Copying files from ${src} to ${dest}...`);
	}
	await Bluebird.mapSeries(srcFiles, async (srcP) => {
		const destP = Path.join(dest, Path.relative(src, srcP));
		await mkdirp(Path.dirname(destP));
		if (banner || check) {
			const srcContents = await Fs.readFile(srcP, "utf8");
			const destContents = banner
				? addOrReplaceCodegenBanner(srcContents, {
						destP,
						srcP,
						root,
					})
				: srcContents;
			if (check) {
				try {
					const origContents = await Fs.readFile(destP, "utf8");
					const origWithBanner = banner
						? addOrReplaceCodegenBanner(origContents, {destP, srcP, root})
						: origContents;
					if (destContents !== origWithBanner) {
						console.log(`  CHECK FAILED: ${destP} does not match ${srcP}`);
						checkError = true;
					}
				} catch (ex: any) {
					if (ex && ex.code === "ENOENT") {
						console.log(
							`  CHECK FAILED: ${destP} does not exist but ${srcP} exists`
						);
						checkError = true;
					} else {
						throw ex;
					}
				}
			} else {
				console.log(`  Copying ${srcP} to ${destP} with banner...`);
				await Fs.writeFile(destP, destContents, "utf8");
			}
		} else {
			console.log(`  Copying ${srcP} to ${destP}...`);
			await Fs.copyFile(srcP, destP);
		}
	});

	return !(check && checkError);
}

type GenBannerProps = {
	destP: string;
	srcP: string;
	root?: string;
	withDelims?: boolean;
};

function makeCodegenBanner(props: GenBannerProps): string {
	const {destP, srcP, root = "", withDelims = false} = props;
	// If we do ES modules, replace __filename with new URL("", import.meta.url)
	const ownPath = __filename;
	const dispOwnPath = root ? Path.relative(root, ownPath) : ownPath;
	const dispSrcP = root ? Path.relative(root, srcP) : srcP;

	const ext = Path.extname(destP).toLowerCase();
	if ([".js", ".jsx", ".ts", ".tsx"].includes(ext)) {
		let base = `
			/**
			 * NOTE: CODEGEN IS USED IN THIS FILE. Careless manual edits may be lost.
			 *
			 * ${dispOwnPath} keeps this file in sync with:
			 *   ${dispSrcP}
			 *
			 * You can run it with the following command:
			 * 	npm run gen-sync-shared
			 */
			`.trim();
		if (withDelims) {
			base =
				"//@@ BEGIN CODEGEN WARNING\n" + base + "\n//@@ END CODEGEN WARNING";
		}
		return base.trim().replace(/\n\t+/g, "\n") + "\n\n";
	} else if ([".yaml", ".yml"].includes(ext)) {
		let base = `
			# NOTE: CODEGEN IS USED IN THIS FILE. Careless manual edits may be lost.
			#
			# ${dispOwnPath} keeps this file in sync with:
			#   ${dispSrcP}
			`.trim();
		if (withDelims) {
			base = "#@@ BEGIN CODEGEN WARNING\n" + base + "\n#@@ END CODEGEN WARNING";
		}
		return base.trim().replace(/\n\t+/g, "\n") + "\n\n";
	} else if ([".md"].includes(ext)) {
		return "";
	}
	console.error(`WARNING: ${destP} has unknown extension; no banner`);
	return "";
}

function addOrReplaceCodegenBanner(
	oldContents: string,
	bannerProps: GenBannerProps
): string {
	let newContents = "";
	try {
		const bannerText = makeCodegenBanner(bannerProps);
		newContents = replaceBody({
			src: oldContents,
			begin: /[\/#]*@@ BEGIN CODEGEN WARNING/,
			end: /[\/#]*@@ END CODEGEN WARNING/,
			newBody: bannerText.trim(),
			throwIfNotFound: true,
		});
	} catch (error) {
		if (error instanceof Error && error.message === "E_BEGIN_DELIM_NOT_FOUND") {
			const bannerText = makeCodegenBanner({...bannerProps, withDelims: true});
			// no preexisting banner, just prepend one
			newContents = bannerText + oldContents;
		} else {
			throw error;
		}
	}
	return newContents;
}

run(main);
