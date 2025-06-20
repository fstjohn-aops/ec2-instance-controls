// Various helpers for working with Platform, such as checkSession

import {cookies, headers} from "next/headers";
import {redirect} from "next/navigation";
import type {ReadonlyHeaders} from "next/dist/server/web/spec-extension/adapters/headers";

import type {
	PlatformSession,
	FastContext,
	PlatformAgent,
} from "@aops-trove/fast-auth";
import {extRequest} from "@aops-trove/fast-ext-request";
import {createCookieApiForNextJs} from "@aops-trove/fast-cookie/Next";
import {getRedis} from "./Redis";
import {log} from "./Logger";
import {IS_DEV} from "./General";
import {initPlaccSdk} from "@aops-trove/placc-sdk";
import Redis from "ioredis";
const FALLBACK_IP = "127.0.0.1";

// Right now fast-auth calls it FastContext, but it should be renamed.
export async function createPlatformContext(): Promise<FastContext> {
	const redis = await getRedis();
	return {
		selfOrigin: process.env.NEXT_PUBLIC_NEXTJS_BASE_URL!,
		plogOrigin: process.env.NEXT_PUBLIC_PLATFORM_LOGIN_URL!,
		applicationCode: getApplicationCode(),
		devApplicationCode: await getDevApplicationCode(redis),
		gatewayUrl: process.env.PLATFORM_URL!,
		platformApiKey: process.env.SECRET_PLATFORM_API_KEY!,
		redis,
		cookies: createCookieApiForNextJs({
			cookies: cookies(),
			headers: headers(),
			cookieSignatureKey: process.env.SECRET_COOKIE_SIGNATURE_KEY!,
			cookieSignatureKeyOld: process.env.SECRET_COOKIE_SIGNATURE_KEY_OLD,
			createOpts: {isDev: IS_DEV},
		}),
		replyRedirect: (url) => redirect(url),
		log,
	};
}

export async function getPlaccSdk(
	params: {
		sessionId?: string;
		userId?: string;
	} = {}
) {
	const {sessionId, userId} = params;
	const redis = await getRedis();

	const placcSdk = initPlaccSdk({
		baseUrl: process.env.PLATFORM_URL!,
		apiKey: process.env.SECRET_PLATFORM_API_KEY!,
		extRequest: (params: any) => extRequest(log, params),
		redis,
		log,
		agent: {
			applicationCode: getApplicationCode(),
			devApplicationCode: await getDevApplicationCode(redis),
			ip: getIp(headers()),
			userAgent: headers().get("user-agent") ?? undefined,
			sessionId,
			userId,
		},
		//These are optional parameters, configure as needed. These are best guesses at defaults.
		checkBodyType: {
			throwErrorOnFail: IS_DEV,
			logLevelOnFail: "error",
		},
		checkResponseType: {
			throwErrorOnFail: IS_DEV,
			logLevelOnFail: "error",
		},
	});
	return placcSdk;
}

export type AgentInput = {
	method: string;
	session?: PlatformSession;
};
export async function getPlatformAgent(
	props: AgentInput
): Promise<PlatformAgent & {ip: string}> {
	const h = headers();
	const redis = await getRedis();

	return {
		method: props.method,
		applicationCode: getApplicationCode(),
		devApplicationCode: await getDevApplicationCode(redis),
		sessionId: props.session?.sessionId,
		userId: props.session?.userId,
		ip: getIp(h),
		userAgent: h.get("user-agent") ?? undefined,
	};
}

export function getIp(h: ReadonlyHeaders) {
	let ip: string =
		h.get("cf-connecting-ip") ||
		h.get("x-real-ip") ||
		h.get("x-forwarded-for") ||
		FALLBACK_IP;
	if (ip && ip.includes(",")) {
		ip = ip.split(",")[0];
	}
	return ip.trim();
}

export function getApplicationCode(): string {
	if (!process.env.APPLICATION_CODE) {
		throw new Error(`process.env.APPLICATION_CODE has no value.`);
	}
	return process.env.APPLICATION_CODE;
}

export async function getDevApplicationCode(
	redis: Redis
): Promise<string | undefined> {
	if (!IS_DEV) {
		return undefined;
	}

	const devApplicationCode = await redis.get("devApplicationCode");
	return devApplicationCode ?? undefined;
}
