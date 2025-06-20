// This file specifies custom Fastify types, e.g. from decorators. It uses the
// declaration merging pattern as recommended by Fastify:
// https://www.fastify.io/docs/latest/TypeScript/

// Without this line, this file overrides types instead of merging.
import "fastify";

import {Redis} from "ioredis";
import {ExtRequestFunc} from "@aops-trove/fast-ext-request";
import {ProjectConfig} from "./init/ProjectConfig";
import {Knex} from "knex";

declare module "fastify" {
	interface FastifyInstance {
		projectConfig: ProjectConfig;
		redis: Redis;
		knex: Knex;
	}
	interface FastifyRequest {
		extRequest: ExtRequestFunc;
	}
	interface FastifyReply {
		payload: unknown;
	}
	interface FastifyContextConfig {
		requireApiKey?: boolean;
	}
}
