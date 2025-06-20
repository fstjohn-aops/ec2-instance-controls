import run from "./util/Run";
import Yargs from "yargs";
import {hideBin} from "yargs/helpers";

import _ from "lodash";

type Args = {
	notes?: string;
};

async function main() {
	const argv: Args = await Yargs(hideBin(process.argv))
		.strictOptions()
		.help()
		.version(false)
		.usage("A sample script that shows good practices for writing files here")
		.option("notes", {
			describe: "A string that the script will excitedly print to stdout.",
			type: "string",
		}).argv;

	if (argv.notes) {
		console.log("We got a notes option! Contents:");
		console.log(argv.notes);
		console.log("");
	}

	console.log("_.each([1,2,3], ...");
	_.each([1, 2, 3], (x) => {
		console.log(x, "Returning x === 1");
		return x === 1;
	});
	console.log("_.each loop end", "(notice the return false short circuit?)");
	console.log("");
}

run(main);
