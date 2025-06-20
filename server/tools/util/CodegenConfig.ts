/**
 * Utility for finding codegen configuration in a source file. Companion to
 * StringSplice.
 *
 * Usually codegen config in a source file looks like
 *   //@@ varName = value is any string
 *   //@@ anotherVar = search continues until no //@@
 *   //@@ BEGIN (codegen marker)
 * However, some of this is configurable.
 */

import {escapeRegex} from "./StringSplice";

type FindConfigParams = {
	src: string;
	begin: string;
	prefix?: string;
};

type FindConfigReturn = {[name: string]: string};

/**
 * Provide a source string, a begin delimiter, and a prefix for lines with
 * config values (default "//@@"). This finds the begin delimiter, then reverse
 * searches the beginning of each line for the prefix followed by a var = value
 * pattern. The search stops when any line not starting with the prefix
 * (ignoring white space) is found.
 *
 * The return is an object of string values with each found var = value line.
 * All characters are accepted in the value except line breaks and terminating
 * whitespace.
 *
 * There are currently no options to perform the search on anything other
 * than the first match of the begin delimiter, but this could be added.
 */
export function findCodegenConfig(
	params: FindConfigParams
): FindConfigReturn | null {
	const {src, begin, prefix = "//@@"} = params;

	const beginLineRegex = new RegExp(
		"^([ \t]*)" + escapeRegex(begin) + "[ \t]*$",
		"m"
	);
	const beginLineMatch = beginLineRegex.exec(src);
	if (!beginLineMatch) {
		return null;
	}

	const configValueRegex = new RegExp("^([a-zA-Z0-9_$]+)[ \t]*=[ \t]*(.*)$");

	let currLinePos = beginLineMatch.index;
	const returnedConfig: FindConfigReturn = {};
	while (currLinePos > 0) {
		const previousLineBreakPos = src
			.slice(0, currLinePos - 1)
			.lastIndexOf("\n");
		// Below var works even if above returns -1
		const previousLinePos = previousLineBreakPos + 1;
		const configLine = src.slice(previousLinePos, currLinePos).trim();
		if (!configLine.startsWith(prefix)) {
			break;
		}
		const configValueRaw = configLine.slice(prefix.length).trim();
		const configValueMatch = configValueRegex.exec(configValueRaw);
		if (!configValueMatch) {
			continue;
		}
		returnedConfig[configValueMatch[1]!] = configValueMatch[2]!;
		currLinePos = previousLinePos;
	}
	return returnedConfig;
}
