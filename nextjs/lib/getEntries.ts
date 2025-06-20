/**
 * Example of using a Fastify API endpoint.
 */

import {entriesResponseT} from "./shared/Entries";
import {makeOurFastifyRequest} from "./OurFastify";
import {Static} from "@sinclair/typebox";
import {checkSession} from "./Session";

export async function getEntries(): Promise<Static<
	typeof entriesResponseT
> | null> {
	const session = await checkSession();
	if (!session) {
		return null;
	}

	const entries = await makeOurFastifyRequest("api/v1/entries", "GET", {});
	return entries;
}
