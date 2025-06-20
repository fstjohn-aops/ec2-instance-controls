/**
 * Utility for mocking the extRequest function. Rather than just be a plain
 * mock function, this forces all mocking and call logging to be grouped by
 * URL, which hopefully makes tests using this more fluent. Note that any
 * use of extRequest on a URL will throw if not set up beforehand.
 */

import {
	ExtRequestParams,
	ExtRequestResponse,
	ExtRequestFunc,
} from "@aops-trove/fast-ext-request";

type HandledUrls = {[url: string]: jest.MockedFunction<any>};

export type MockExtRequest = {
	handledUrls: HandledUrls;
	totalCalls: number;
	fn: ExtRequestFunc;
};

/**
 * The main export. Returns an object, of which fn is the extRequest function
 * suitable to include in a route input object. The other properties are for
 * internal tracking; prefer to use other functions in this file rather than
 * interface with those properties directly.
 */
export function makeMockExtRequest(): MockExtRequest {
	const handledUrls: HandledUrls = {};
	async function fn(params: ExtRequestParams): Promise<ExtRequestResponse> {
		m.totalCalls += 1;
		const method = params.method || "GET";
		const url = params.url;
		const candKeys = getUrlTableKeysToCheck(method, url);
		const availKeys = candKeys.filter((k) => handledUrls[k]);
		if (!availKeys.length) {
			throw new Error(
				"Called extRequest for unrecognized URL: " + candKeys[0]!
			);
		}
		const handler = handledUrls[availKeys[0]!];
		return handler(params);
	}
	const m: MockExtRequest = {
		handledUrls,
		totalCalls: 0,
		fn,
	};
	return m;
}

/**
 * Given a MockExtRequest return, get the total calls across all URLs.
 */
export function getTotalCalls(m: MockExtRequest): number {
	return m.totalCalls;
}

/**
 * Provide a method and URL that MockExtRequest should allow calls for. Returns
 * the Jest MockedFunction that will log all requests to that URL. Method can
 * be * to handle all methods for a URL.
 */
export function setupUrl(
	m: MockExtRequest,
	method: string,
	url: string
): jest.MockedFunction<ExtRequestFunc> {
	const fn = jest.fn();
	const key = getUrlTableKeysToCheck(method, url)[0]!;
	m.handledUrls[key] = fn;
	return fn;
}

// Internal helper. Get the keys on m.handledUrls to check for handling a
// mocked external request. The first element is assumed to be a unique to the
// passed arguments.
function getUrlTableKeysToCheck(method: string, url: string): string[] {
	return [method.toUpperCase() + " " + url, "* " + url];
}
