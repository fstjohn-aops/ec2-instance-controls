// @ts-ignore (no @types repo? prob doesn't need any though)
import Redis from "ioredis-mock";
import {Redis as RealRedisType} from "ioredis";

let redisNeedsClear = false;

export function makeMockRedis() {
	redisNeedsClear = true;
	const redis: RealRedisType = new Redis();
	return redis;
}

/**
 * Global Jest hook to clean up redis after each test.
 */
afterEach(async () => {
	if (redisNeedsClear) {
		const redis = new Redis();
		await redis.flushall();
		redisNeedsClear = false;
	}
});
