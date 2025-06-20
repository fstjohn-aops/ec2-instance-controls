/**
 * Plugin for doing API key checks on all requests.
 */

import {FastifyInstance, FastifyRequest, FastifyReply} from "fastify";
import fp from "fastify-plugin";

/**
 * Register a plugin that adds an API key check to all requests.
 *
 * @param server {object}
 */
export function initApiKey(server: FastifyInstance) {
	server.register(fp(pluginApiKey));
}

async function pluginApiKey(server: FastifyInstance) {
	const {apiKey} = server.projectConfig || {};

	if (!apiKey) {
		throw new Error("No API key was specified in config.yaml.");
	}

	server.addHook(
		"preHandler",
		async function (request: FastifyRequest, reply: FastifyReply) {
			const key = request.headers["x-api-key"];

			if (!request.routeOptions.config.requireApiKey || key === apiKey) {
				// OK
			} else {
				const source = getRequestSource(request);
				const message = key ? "Incorrect API key sent" : "No API key sent";
				request.log.warn(
					{
						module: "ApiKey",
						fn: "preHandler",
						label: "BadApiKey",
						...source,
					},
					message
				);

				reply.code(401);
				reply.send("Invalid API Key");
				return reply;
			}
		}
	);
}

function getRequestSource(request: FastifyRequest): object {
	return {
		origin: request.headers["origin"],
		referer: request.headers["referer"],
		userAgent: request.headers["user-agent"],
	};
}
