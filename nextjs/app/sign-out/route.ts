import {createPlatformContext} from "@/lib/Platform";
import {handlerForSignOut} from "@aops-trove/fast-auth";
import {NextRequest} from "next/server";

export async function GET(request: NextRequest) {
	const ctx = await createPlatformContext();
	const qs = request.nextUrl.searchParams;
	return handlerForSignOut({
		ctx,
		redirect: qs.get("redirect") ?? undefined,
	});
}
