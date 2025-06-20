/**
 * Utilities for interfacing with this project's Fastify server, which is
 * being referred to as OurFastify.
 */

import {extRequest} from "@aops-trove/fast-ext-request";
import {isMethodDisallowingBody} from "@aops-trove/fast-server-common";
import {log} from "./Logger";

export async function makeOurFastifyRequest(
	url: string,
	method: string,
	payload: any
): Promise<any> {
	const useQuery = isMethodDisallowingBody(method);

	return extRequest(log, {
		url: `${process.env.FASTIFY_BASE_URL}/${url}`,
		method,
		headers: {
			"x-api-key": process.env.SECRET_FASTACK_STARTER_API_KEY ?? "",
		},
		body: useQuery ? undefined : payload,
		query: useQuery ? payload : undefined,
	});
}
