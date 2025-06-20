import {headers} from "next/headers";
import {
	checkSession as checkSessionFastAuth,
	handlerForSignIn,
	PlatformSession,
} from "@aops-trove/fast-auth";
import {createPlatformContext, getPlatformAgent} from "./Platform";

export function getSignInUrl(overridePath?: string) {
	let redirectPath = overridePath ?? getRequestPath();
	if (redirectPath && !redirectPath.startsWith("/")) {
		redirectPath = "/" + redirectPath;
	}
	const redirect = encodeURIComponent(
		`${process.env.NEXT_PUBLIC_NEXTJS_BASE_URL}${redirectPath}`
	);
	return `/sign-in?redirect=${redirect}`;
}

export function getSignOutUrl(overridePath?: string) {
	let redirectPath = overridePath ?? getRequestPath();
	if (redirectPath && !redirectPath.startsWith("/")) {
		redirectPath = "/" + redirectPath;
	}
	const redirect = encodeURIComponent(
		`${process.env.NEXT_PUBLIC_NEXTJS_BASE_URL}${redirectPath}`
	);
	return `/sign-out?redirect=${redirect}`;
}

export async function checkSession(): Promise<PlatformSession | null> {
	const ctx = await createPlatformContext();
	const {session} = await checkSessionFastAuth({
		ctx,
		agent: await getPlatformAgent({method: "checkSession"}),
	});
	return session;
}

export async function checkSessionOrRedirect(): Promise<PlatformSession & {}> {
	const ctx = await createPlatformContext();
	const session = await checkSession();
	if (session) {
		return session;
	}

	const reqPath = getRequestPath();
	handlerForSignIn({
		ctx,
		redirect: reqPath ?? undefined,
	});
	// Should not get here
	throw new Error("Expected handlerForSignIn to redirect (throw)");
}

function getRequestPath(): string | null {
	// Gets header set in middleware.
	const h = headers();
	return h.get("x-reqpath");
}
