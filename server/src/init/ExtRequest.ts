/**
 * Plugin for attaching extRequest with a prefilled log parameter on a
 * Fastify request.
 */

import {FastifyInstance, FastifyRequest} from "fastify";
import fp from "fastify-plugin";
import {ExtRequestFunc, extRequest} from "@aops-trove/fast-ext-request";

/**
 * Register a plugin that adds extRequest as a field on Fastify requests.
 *
 * @param server {object}
 */
export function initExtRequest(server: FastifyInstance) {
	server.register(fp(pluginExtRequest));
}

async function pluginExtRequest(server: FastifyInstance) {
	server.decorateRequest("extRequest", null);

	server.addHook("preHandler", async function (request: FastifyRequest) {
		const filledExtRequest: ExtRequestFunc = (params: any) =>
			extRequest(request.log, params);
		request.extRequest = filledExtRequest;
	});
}
