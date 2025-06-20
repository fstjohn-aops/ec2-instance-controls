/**
 * Utilities for splicing into strings. Often used for codegen purposes.
 */

import _ from "lodash";

type ReplaceBodyParams = {
	src: string;
	begin: string | RegExp;
	end: string | RegExp;
	newBody: string;
	ignoreIndent?: boolean;
	throwIfNotFound?: boolean;
};

/**
 * Provide a source string, a begin delimiter, an end delimiter, and a new body
 * to replace text between the begin and end. This will find the first line
 * equal to the begin delimiter, find the next line after equal to the end
 * delimiter, and replace all the lines between the two with the new body.
 *
 * When matching begin and end, beginning and ending white space are ignored,
 * both in the line and in the passed argument.
 *
 * There are currently no options to perform the replacement on anything other
 * than the first match, but this could be added.
 *
 * Other options:
 * - ignoreIndent: By default, the indentation of the begin line is applied to
 *   each line of newBody. Pass true here to suppress that.
 * - throwIfNotFound: By default, src is returned unmodified if the begin and
 *   end delimiters are not found. Pass true here to throw instead.
 */
export function replaceBody(params: ReplaceBodyParams): string {
	const {
		src,
		begin,
		end,
		newBody,
		ignoreIndent = false,
		throwIfNotFound = false,
	} = params;

	function handleNotFound(err: string) {
		if (throwIfNotFound) {
			throw new Error(err);
		}
		return src;
	}

	const beginStr = _.isString(begin)
		? escapeRegex(begin)
		: begin.toString().slice(1, begin.toString().length - 1); // remove leading/trailing slashes
	const beginLineRegex = new RegExp("^([ \t]*)" + beginStr + "[ \t]*$", "m");
	const beginLineMatch = beginLineRegex.exec(src);
	if (!beginLineMatch) {
		return handleNotFound("E_BEGIN_DELIM_NOT_FOUND");
	}
	const beginIndent = beginLineMatch[1];
	const beginLineEnd = beginLineMatch.index + beginLineMatch[0]!.length;

	const endStr = _.isString(end)
		? escapeRegex(end)
		: end.toString().slice(1, end.toString().length - 1); // remove leading/trailing slashes
	const endLineRegex = new RegExp("^\\s*" + endStr + "\\s*$", "m");
	const endLineMatch = endLineRegex.exec(src.slice(beginLineEnd));
	if (!endLineMatch) {
		return handleNotFound("E_END_DELIM_NOT_FOUND");
	}
	const endLineStart = endLineMatch.index + beginLineEnd;

	function indentLine(l: string) {
		if (/^\s*$/.test(l)) {
			return "";
		}
		return beginIndent + l;
	}

	let newBodyIndented = newBody;
	if (!ignoreIndent) {
		const newBodyLines = newBodyIndented.split("\n");
		newBodyIndented = newBodyLines.map(indentLine).join("\n");
	}
	if (!newBodyIndented.endsWith("\n")) {
		newBodyIndented += "\n";
	}
	return (
		src.slice(0, beginLineEnd) +
		"\n" +
		newBodyIndented +
		src.slice(endLineStart)
	);
}

/**
 * Escape regexp special characters in a string. From
 * https://stackoverflow.com/a/3561711.
 */
export function escapeRegex(str: string): string {
	return str.replace(/[-\/\\^$*+?.()|[\]{}]/g, "\\$&");
}
