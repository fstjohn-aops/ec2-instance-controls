import {NextResponse} from "next/server";
import type {NextRequest} from "next/server";

// Login redirects need to know current URL, which NextJS strangely makes very
// difficult to obtain. Inspired from
// https://www.propelauth.com/post/getting-url-in-next-server-components
export function middleware(request: NextRequest) {
	const headers = new Headers(request.headers);
	headers.set("x-reqpath", request.nextUrl.pathname);
	return NextResponse.next({request: {...request, headers}});
}

export const config = {
	matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
