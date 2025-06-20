import {Redis} from "ioredis";
import Os from "os";
import {IS_DEV} from "../util/General";

export async function initDevApplicationCode(redis: Redis) {
	if (!IS_DEV) {
		return;
	}

	const devApplicationCode = Os.hostname();
	await redis.set("devApplicationCode", devApplicationCode);

	// Reset the cache every second
	setInterval(async () => {
		await redis.set("devApplicationCode", devApplicationCode);
	}, 1000);

	return devApplicationCode;
}

export async function getDevApplicationCode(redis: Redis) {
	if (!IS_DEV) {
		return undefined;
	}

	const devApplicationCode = await redis.get("devApplicationCode");
	return devApplicationCode ?? undefined;
}
