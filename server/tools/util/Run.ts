/**
 * Small utility to wrap the main function of a script and provide a good
 * error handling / timeout foundation.
 */

export type CleanupFunc = (err: any) => Promise<void>;

export type RunOpts = {
	cleanup?: CleanupFunc;
	timeout?: number;
};

const WARN_TIMEOUT = `
WARNING: The script's main function finished, but the process did not exit
naturally before reaching a timeout. Exiting...
`.trim();

const registeredCleanupFunctions: CleanupFunc[] = [];

export default async function run(
	main: () => Promise<void>,
	options: RunOpts = {}
): Promise<void> {
	const {cleanup, timeout = 1000} = options;
	if (cleanup) {
		registerCleanupFunction(cleanup);
	}

	let err;
	try {
		await main();
	} catch (ex) {
		console.error("main rejected", ex);
		process.exitCode = 1;
		err = ex;
	}
	let i = 0;
	for (const cleanupFunc of registeredCleanupFunctions) {
		try {
			// eslint-disable-next-line no-await-in-loop
			await cleanupFunc(err);
		} catch (ex) {
			console.error("cleanup[" + i + "] rejected", ex);
			process.exitCode = 1;
		}
		i += 1;
	}

	if (timeout && timeout > 0) {
		const t = setTimeout(() => {
			console.error(WARN_TIMEOUT);
			process.exit();
		}, timeout);
		t.unref();
	}
}

export function registerCleanupFunction(newFunc: CleanupFunc) {
	registeredCleanupFunctions.push(newFunc);
}
