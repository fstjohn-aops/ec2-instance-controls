/**
 * Small utility to have prettier do a pass when you have a file path and the
 * contents you will write to it.
 */

import Prettier from "prettier";

export async function runPrettier(filePath: string, contents: string) {
	try {
		const prettierConfig = await Prettier.resolveConfig(filePath);
		if (!prettierConfig) {
			console.error(
				"WARNING: Prettier config could not be found. Skipping prettier run."
			);
		} else {
			contents = await Prettier.format(contents, {
				filepath: filePath,
				...prettierConfig,
			});
		}
	} catch (ex: any) {
		console.error(
			"WARNING: Prettier run failed with below error. Skipping prettier run."
		);
		console.error("Prettier error", ex);
	}
	return contents;
}
