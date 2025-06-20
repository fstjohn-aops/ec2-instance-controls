import {headers} from "next/headers";

/**
 * Call this when you want to force NextJS to do dynamic rendering on a page.
 * Currently used in places like the Redis connection that will fail during a
 * Docker build.
 *
 * @see https://nextjs.org/docs/app/building-your-application/rendering/server-components#dynamic-functions
 */
export function forceDynamic() {
	// unstable_noStore might be a better way in a future version, but will hold
	// off while it's unstable.
	headers();
}
