/**
 * Code for managing configuration variables that can be updated at runtime via
 * API. Uses redis pubsub to support both runtime updates and sync access of
 * values.
 */

import _ from "lodash";
import {Redis as RedisType} from "ioredis";
import {
	assertNever,
	TimeUnit,
	convertTimeUnit,
	RequestError,
	ServerError,
	makeLoggableError,
	LogApi,
} from "@aops-trove/fast-server-common";
import {IS_DEV} from "../util/General";

/**
 * Defines the type and defaults for each config variable.
 *
 * Each value is of type RtConfigDefn, but we need to let Typescript infer
 * things here to smartly detect the proper type of each config variable.
 */
const valueDefns = {
	cronsDisabled: {
		type: "boolean",
		description: "If true, skip running crons and mark them completed",
	},
	testInt: {
		type: "int",
		defaultValue: 5,
		description: "Unused; just giving TS/tests an int var to work with",
	},
	testFloat: {
		type: "float",
		defaultValue: 30,
		description: "Unused; just giving TS/tests a float var to work with",
	},
	testFloatInDays: {
		type: "float",
		defaultValue: 30,
		timeUnit: "days",
		description: "Unused; just giving TS/tests a float var to work with",
	},
	testFloatInHours: {
		type: "float",
		defaultValue: 2,
		timeUnit: "hours",
		description: "Unused; just giving TS/tests a float var to work with",
	},
	testString: {
		type: "string",
		description: "Unused; just giving TS/tests a string var to work with",
	},
} as const;

export type RtConfigName = keyof typeof valueDefns;

export type RtConfigType = "boolean" | "int" | "float" | "string";

export type RtConfigDefn =
	| {
			type: "boolean";
			defaultValue?: boolean;
			description?: string;
	  }
	| {
			type: "int" | "float";
			defaultValue?: number;
			timeUnit?: TimeUnit;
			description?: string;
	  }
	| {
			type: "string";
			defaultValue?: string;
			description?: string;
	  };

type RtConfigTypeMapping = {
	boolean: boolean;
	int: number;
	float: number;
	string: string;
};

type RtConfigValueType = RtConfigTypeMapping[RtConfigType];

export type RtConfigValues = {
	[K in RtConfigName]: RtConfigTypeMapping[(typeof valueDefns)[K]["type"]];
};

/**
 * Array with all config variables.
 */
const configNames: RtConfigName[] = Object.keys(valueDefns) as any;

/**
 * Object with all current config values. Mutated during runtime.
 */
const currValues: RtConfigValues = _.mapValues(valueDefns, (_v, k: any) =>
	getDefaultValue(k)
);

/**
 * Module-level state with whether we are currently operating in single-process
 * mode.
 */
let singleProcessMode = false;

/**
 * Internal helper. Computes the default of a variable.
 */
function getDefaultValue<K extends RtConfigName>(name: K): RtConfigValues[K] {
	const spec: RtConfigDefn = valueDefns[name];
	if (!spec) {
		throw new ServerError("E_RTCONFIG_INVALID_NAME", {
			moreInfo: {name},
		});
	} else if (spec.defaultValue !== undefined) {
		return spec.defaultValue as any;
	} else if (spec.type === "boolean") {
		return false as any;
	} else if (spec.type === "int" || spec.type === "float") {
		return 0 as any;
	} else if (spec.type === "string") {
		return "" as any;
	} else {
		return assertNever(spec.type, () => {
			throw new Error("Invalid RtConfig value type " + spec.type);
		});
	}
}

/**
 * Internal helper. Turns a string taken out of redis into the correct type.
 */
function parseValue<K extends RtConfigName>(
	name: K,
	value: string | undefined
): RtConfigValueType {
	const spec: RtConfigDefn = valueDefns[name];
	if (!spec) {
		throw new ServerError("E_RTCONFIG_INVALID_NAME", {
			moreInfo: {name},
		});
	} else if (value === undefined) {
		return getDefaultValue(name);
	} else if (spec.type === "boolean") {
		return value !== "" && value !== "0" && value.toLowerCase() !== "false";
	} else if (spec.type === "int") {
		const prelim = parseInt(value);
		return _.isFinite(prelim) ? prelim : getDefaultValue(name);
	} else if (spec.type === "float") {
		const prelim = parseFloat(value);
		return _.isFinite(prelim) ? prelim : getDefaultValue(name);
	} else if (spec.type === "string") {
		return value;
	} else {
		return assertNever(spec.type, () => {
			throw new Error("Invalid RtConfig value type " + spec.type);
		});
	}
}

/**
 * Initializes the system, including starting a subscribing redis connection.
 * Returns that new redis connection; make sure to clean it up at shutdown.
 *
 * No cleanup other than quitting the redis subscriber is needed. If you need
 * to initialize multiple times, like in tests, just call init with the desired
 * redis connection to overwrite all existing state. You may also want to call
 * resetAll in an after hook.
 */
export async function initRuntimeConfig(
	createRedisConnection: () => RedisType,
	redis: RedisType,
	log: LogApi
): Promise<RedisType> {
	await resyncFromRedis(redis, log);
	singleProcessMode = false;
	const redisSub = watchForChanges(createRedisConnection, redis, log);

	log.info(
		{
			module: "RuntimeConfig",
			step: "init",
			singleProcessMode,
		},
		"Initialized RuntimeConfig"
	);

	return redisSub;
}

/**
 * Initializes the system except assuming this is the only process subscribing to
 * updates. Skips Redis pubsub. Very useful for tests.
 */
export async function initRuntimeConfigForSingleProcess(
	redis: RedisType,
	log?: LogApi
): Promise<void> {
	await resyncFromRedis(redis, log);
	singleProcessMode = true;

	log &&
		log.info(
			{
				module: "RuntimeConfig",
				step: "init",
				singleProcessMode,
			},
			"Initialized RuntimeConfig in single-process mode"
		);
}

/**
 * Returns a boolean with whether the passed name is a valid variable.
 */
export function isValidName(name: string): name is RtConfigName {
	return name in valueDefns;
}

/**
 * Returns an object mapping each variable to its RtConfigDefn object.
 */
export function getDefns(): typeof valueDefns {
	return valueDefns;
}

/**
 * Returns an object containing all of the current RuntimeConfig values.
 */
export function getAll(): RtConfigValues {
	return _.clone(currValues);
}

/**
 * Returns the value of the specified RuntimeConfig variable.
 */
export function getValue<K extends RtConfigName>(name: K): RtConfigValues[K] {
	const value = currValues[name];
	if (value !== undefined) {
		return value;
	}

	// This is already unexpected.
	if (IS_DEV) {
		throw new ServerError("E_RTCONFIG_NO_VALUE", {
			moreInfo: {name},
		});
	}
	return getDefaultValue(name);
}

/**
 * Sets all variables to their default values and notifies all processes of the
 * change through redis pubsub.
 */
export async function resetAll(redis: RedisType) {
	await redis.del("rtconfig:values");
	if (singleProcessMode) {
		await resyncFromRedis(redis);
	} else {
		await redis.publish("fastackstarter:rtconfig:changed", "*");
	}
}

/**
 * Sets one variable's value and notifies all processes of the change through
 * redis pubsub.
 */
export async function setValue(
	redis: RedisType,
	name: RtConfigName,
	value: RtConfigValueType | null
) {
	const spec: RtConfigDefn = valueDefns[name];
	const valueTypeIsOk =
		value === null ||
		(spec.type === "boolean" && typeof value === "boolean") ||
		(spec.type === "int" && typeof value === "number") ||
		(spec.type === "float" && typeof value === "number") ||
		(spec.type === "string" && typeof value === "string");
	if (!valueTypeIsOk) {
		throw new RequestError("E_RTCONFIG_INVALID_VALUE", {
			moreInfo: {name, value, expectedType: spec.type},
		});
	}
	if (value === null) {
		await redis.hdel("rtconfig:values", name);
	} else {
		await redis.hset("rtconfig:values", name, String(value));
	}
	if (singleProcessMode) {
		await resyncFromRedis(redis);
	} else {
		await redis.publish("fastackstarter:rtconfig:changed", name);
	}
}

/**
 * Variant of setValue that accepts a number and a time unit. Only usable with
 * RuntimeConfig variables that represent time intervals, corresponding to a
 * timeUnit value on their defn.
 */
export async function setTimeValue(
	redis: RedisType,
	name: RtConfigName,
	value: number,
	timeUnit: TimeUnit
) {
	const spec = valueDefns[name];
	const baseUnit = spec && "timeUnit" in spec ? spec.timeUnit : null;
	if (!baseUnit) {
		throw new RequestError("E_RTCONFIG_INVALID_NAME_FOR_TIME", {
			moreInfo: {name},
		});
	}
	const realValue = convertTimeUnit(value, timeUnit, baseUnit);
	await setValue(redis, name, realValue);
}

/**
 * Internal helper. Reloads all variables from redis. Used as the listener for
 * the Redis subscribe command.
 */
async function resyncFromRedis(redis: RedisType, log?: LogApi) {
	const values = await redis.hgetall("rtconfig:values");
	configNames.forEach((k) => {
		// @ts-expect-error
		currValues[k] = parseValue(k, values[k]);
	});

	log &&
		log.info(
			{
				module: "RuntimeConfig",
				step: "load",
			},
			"RuntimeConfig values loaded from redis"
		);
}

/**
 * Internal helper. Called on initialization to set up the Redis subscriber.
 */
function watchForChanges(
	createRedisConnection: () => RedisType,
	redis: RedisType,
	log: LogApi
): RedisType {
	const redisSub = createRedisConnection();

	redisSub.subscribe("fastackstarter:rtconfig:changed").catch((ex) => {
		log.error(
			{
				module: "RuntimeConfig",
				step: "subscribe",
				error: makeLoggableError(ex),
			},
			"Error subscribing to redis channel for RuntimeConfig"
		);
	});

	redisSub.on("message", () => {
		log.debug(
			{
				module: "RuntimeConfig",
				step: "resync",
			},
			"Performing RuntimeConfig resync due to channel message"
		);

		resyncFromRedis(redis, log).catch((ex) => {
			log.error(
				{
					module: "RuntimeConfig",
					step: "resyncFail",
					error: makeLoggableError(ex),
				},
				"Error updating RuntimeConfig values from redis"
			);
		});
	});

	return redisSub;
}
