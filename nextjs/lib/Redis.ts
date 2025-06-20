import {initRedis} from "@aops-trove/fast-redis";
import type Redis from "ioredis";
import {forceDynamic} from "./forceDynamic";

let redisSingleton: Redis | undefined;

export async function getRedis(): Promise<Redis> {
	if (redisSingleton) {
		return redisSingleton;
	}

	// Force static rendering (i.e. Docker build) to bail out. This might be
	// improvable if we can make sure Redis is up during any Docker build, but at
	// the moment there's no benefit.
	forceDynamic();

	// We need to use a TLS connection on AWS, but not on local
	const useTls =
		!!process.env.USE_REDIS_TLS || process.env.AWS_EXECUTION_ENV !== undefined;

	// The !s are lies to Typescript, but `parseInt(undefined) || x` gives x.
	const redis = await initRedis({
		redisHost: process.env.REDIS_HOST,
		redisPort: parseInt(process.env.REDIS_PORT!) || undefined,
		redisDb: parseInt(process.env.REDIS_DB!) || undefined,
		redisPassword: process.env.REDIS_PASSWORD,
		tls: useTls,
	});
	redisSingleton = redis;
	return redis;
}
