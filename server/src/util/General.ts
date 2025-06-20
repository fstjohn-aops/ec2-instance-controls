/**
 * Contains miscellaneous utilities. We'll split this up and name it better
 * once it reaches critical mass.
 */

import "dotenv/config";
import * as Fs from "fs";
import * as Path from "path";
import Yaml from "js-yaml";
import _ from "lodash";

/**
 * Path to server root, at server/ in the repo.
 */
export const SERVER_ROOT = Path.join(__dirname, "..", "..");

/**
 * Whether the server is running in Docker. Checked in a hacky way; the
 * Dockerfile writes an empty file and this checks its existence.
 */
export const IS_DOCKER = Fs.existsSync(Path.join(SERVER_ROOT, ".isdocker"));

/**
 * Whether this server is in debug/development mode.
 *
 * If you are inside a route handler, use input.env.dev instead.
 *
 * Note a lot of initialization uses this, so changing it at runtime on config
 * values would be difficult, even if we made it a function instead.
 */
export const IS_DEV = process.env.NODE_ENV !== "production";

// Internal helper var with parsed contents of the package.json file.
// ESM Node doesn't have JSON imports so we get it with Fs.
const packageJson: any = (function () {
	const packagePath = Path.join(SERVER_ROOT, "package.json");
	const contents = Fs.readFileSync(packagePath, "utf8");
	// If this throws, let it. catch handler can't do anything better.
	return JSON.parse(contents);
})();

/**
 * Current version as taken from package.json.
 */
export const PACKAGE_VERSION: string = packageJson.version || "";

/**
 * Load and parse contents of a YAML file synchronously. Used at startup for
 * loading things.
 *
 * @param yamlPath {string}
 * @returns {mixed}
 */
export function loadYAMLSync(yamlPath: string): any {
	const src = Fs.readFileSync(yamlPath, "utf8");
	const parsed = Yaml.load(src);
	return parsed;
}

/**
 * Converts passed object keys to camel case
 */
export function toCamelCase(obj: object): object {
	return _.mapKeys(obj, (_v, k) => _.camelCase(k));
}

/**
 * Converts passed object keys to snake case
 */
export function toSnakeCase(obj: object): object {
	return _.mapKeys(obj, (_v, k) => _.snakeCase(k));
}

/**
 * The Fisher-Yates (aka Knuth) Shuffle
 * https://stackoverflow.com/questions/2450954/how-to-randomize-shuffle-a-javascript-array
 * @param {unknown[]} array
 * @returns {unknown[]} the shuffled array
 */
export function shuffleArray(array: unknown[]): unknown[] {
	let currentIndex = array.length,
		randomIndex;

	// While there remain elements to shuffle.
	while (currentIndex > 0) {
		// Pick a remaining element.
		randomIndex = Math.floor(Math.random() * currentIndex);
		currentIndex--;

		// And swap it with the current element.
		[array[currentIndex], array[randomIndex]] = [
			array[randomIndex],
			array[currentIndex],
		];
	}

	return array;
}

/**
 * Returns a random number from an inclusive interval
 * https://stackoverflow.com/a/7228322
 */
export function randomIntFromInterval(min: number, inclusiveMax: number) {
	return Math.floor(Math.random() * (inclusiveMax - min + 1) + min);
}

/**
 * Shifts one item from a Set
 * @param {Set<T>} set
 * @returns {T}
 */
export function shiftSet<T>(set: Set<T>): T | void {
	for (const value of set) {
		set.delete(value);
		return value;
	}
}

/**
 * Returns a subset of a set.
 * Optional parameter to delete the picked items from the original set.
 * @param {Set<T>} set
 * @param {number} numVal The number of items to shift
 * @param {boolean} toDelete Delete from the original set? Defaults to false.
 * @returns {Set<T>}
 */
export function sliceMultipleFromSet<T>(
	set: Set<T>,
	numVal: number,
	toDelete?: boolean
): Set<T> {
	const values: Set<T> = new Set();
	for (const value of set) {
		if (toDelete) {
			set.delete(value);
		}
		values.add(value);
		if (values.size === numVal) {
			return values;
		}
	}
	return values;
}
