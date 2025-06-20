import {createPlatformContext, getPlatformAgent} from "@/lib/Platform";
import {handlerForFallbackLogin} from "@aops-trove/fast-auth";
import {NextRequest} from "next/server";
import {IS_DEV} from "@/lib/General";

export async function GET(request: NextRequest) {
	const ctx = await createPlatformContext();
	const agent = await getPlatformAgent({method: "fallback-login"});
	const qs = request.nextUrl.searchParams;
	await handlerForFallbackLogin({
		ctx,
		agent,
		code: qs.get("code") ?? undefined,
		redirect: qs.get("redirect") ?? undefined,
		isDev: IS_DEV,
	});
}
