/**
 * Utility for finding all file paths containing a fixed string.
 * Executes grep via shell.
 */

import execa from "execa";

export async function grep(path: string, pattern: string): Promise<string[]> {
	const res = await execa("grep", ["-rl", pattern, path]);
	return res.stdout.split("\n").filter(Boolean);
}
