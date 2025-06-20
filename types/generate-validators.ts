/**
 * This script reads TypeScript type definitions from a file, generates validators using TypeBox,
 * and writes the resulting validators to another file. A codegen warning is prepended to
 * and Prettier is run on the generated file.
 *
 * INPUT_PATH: Path to the TypeScript type definitions file
 * OUTPUT_PATH: Path to the file where validators will be written
 */

import {TypeScriptToTypeBox} from "@sinclair/typebox-codegen";
import {promises as fsp} from "fs";
import {basename} from "path";
import {resolveConfig, format} from "prettier";

const INPUT_PATH = "src/types.ts";
const OUTPUT_PATH = "src/validators-from-types.ts";

generateValidators()
	.then(addExportIfEmpty)
	.then(prependCodegenWarning)
	.then(runPrettier)
	.then(writeToFile)
	.catch((error) => {
		console.error("Error:", error.message);
	})
	.finally(() => {
		console.log(`Generated ${OUTPUT_PATH}`);
	});

/**
 * Generate TypeBox validators from the TypeScript type definitions
 *
 * @returns The generated validators as a string
 * @throws If there is an error generating validators
 */
async function generateValidators(): Promise<string> {
	try {
		const content = await fsp.readFile(INPUT_PATH, "utf-8");

		return TypeScriptToTypeBox.Generate(content);
	} catch (error: unknown) {
		throw new Error(`Error generating validators: ${error}`);
	}
}

/**
 * Add empty export if needed to keep the file a module.
 *
 * @returns "export {};" if nothing was generated
 */
function addExportIfEmpty(content: string) {
	if (content.trim().length === 0) {
		console.warn(
			"src/types.ts has no TypeScript type exports. Exporting {} to stay a module."
		);
		return "export {};";
	}
	return content;
}

/**
 * Prepend a warning comment
 *
 * @param content The content for later writing to `OUTPUT_PATH`
 * @returns The content with the warning comment prepended
 */
function prependCodegenWarning(content: string): string {
	return (
		`/**
		  * NOTE: CODEGEN IS USED IN THIS FILE. Careless manual edits may be lost.
		  *
		  * ${basename(__filename)} keeps this file in sync with:
		  *   ${INPUT_PATH}
		  *
		  * Run with the following command:
		  *   npm run generate
		  */\n` + content
	);
}

/**
 * Format text content using Prettier
 *
 * @param content The content to be formatted
 * @returns The formatted content
 * @throws If Prettier failed to run
 */
async function runPrettier(content: string): Promise<string> {
	try {
		const prettierConfig = await resolveConfig(OUTPUT_PATH);

		if (prettierConfig) {
			const formatted = await format(content, {
				filepath: OUTPUT_PATH,
				...prettierConfig,
			});

			return formatted;
		} else {
			console.error(
				"WARNING: Prettier config could not be found. Skipping prettier run."
			);
		}
	} catch (ex) {
		console.error(
			"WARNING: Prettier run failed with below error. Skipping prettier run."
		);
		console.error("Prettier error", ex);
	}

	return content;
}

/**
 * Write content to `OUTPUT_PATH`
 *
 * @param content The content to write to `OUTPUT_PATH`
 * @throws If there is an error writing to the file
 */
async function writeToFile(content: string): Promise<"ok"> {
	try {
		await fsp.writeFile(OUTPUT_PATH, content);

		return "ok";
	} catch (error: unknown) {
		throw new Error(`Error writing to ${OUTPUT_PATH}: ${error}`);
	}
}
