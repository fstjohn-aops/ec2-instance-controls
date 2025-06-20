import _ from "lodash";
import * as Diff from "diff";

export function diffStrings(str1: string, str2: string): string {
	const changes = Diff.diffLines(str1, str2);
	let lineNumber = 1;
	let addedLineNumber = 1;
	const lineTaggedChanges: {
		lineNumber: number;
		added: boolean;
		content: string;
	}[] = [];

	changes.forEach((c) => {
		const lines = c.value.split("\n");
		const lineCount = lines.length - 1;
		if (c.value.endsWith("\n")) {
			lines.pop();
		}

		if (!c.added && !c.removed) {
			lineNumber += lineCount;
			addedLineNumber = lineNumber;
		} else if (c.removed) {
			lines.forEach((l, i) => {
				lineTaggedChanges.push({
					lineNumber: lineNumber + i,
					added: false,
					content: l,
				});
			});
			lineNumber += lineCount;
		} else {
			lines.forEach((l, i) => {
				lineTaggedChanges.push({
					lineNumber: addedLineNumber + i,
					added: true,
					content: l,
				});
			});
			addedLineNumber += lineCount;
		}
	});

	if (!lineTaggedChanges.length) {
		return "";
	}
	const maxLineNumber = _.last(lineTaggedChanges)!.lineNumber;
	const lineNumberLength = Math.floor(Math.log10(maxLineNumber || 1)) + 1;
	return lineTaggedChanges
		.map((l) => {
			return [
				l.added ? "+" : "-",
				" ",
				_.padStart(String(l.lineNumber), lineNumberLength, " "),
				" |",
				l.content,
				"\n",
			].join("");
		})
		.join("");
}
