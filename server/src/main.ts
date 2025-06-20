/// <reference path="vendor.d.ts" />

import fastify from "fastify";

import {IS_DEV, IS_DOCKER} from "./util/General";

import {initExtRequest} from "./init/ExtRequest";
import {initKnex} from "./init/Knex";
import {initRequestLogging, getLoggingConfig} from "./init/Logging";
import {initProjectConfig} from "./init/ProjectConfig";
import {initRedis, createRedisConnection} from "@aops-trove/fast-redis";
import {initRuntimeConfig} from "./init/RuntimeConfig";
import {initErrorHandlers} from "./init/ServerErrors";

import routeList from "./init/RouteList";
import {wrapRoute, FastackStarterRouteOptions} from "./init/RouteWrap";
import {initCookies} from "@aops-trove/fast-cookie";
import {initApiKey} from "./init/ApiKey";
import {TSchema} from "@sinclair/typebox";
import cors from "@fastify/cors";
import {initDevApplicationCode} from "./init/DevApplicationCode";

async function init() {
	const loggingConfig = getLoggingConfig();
	const server = fastify({
		...loggingConfig,
	});

	initRequestLogging(server);

	const projectConfig = initProjectConfig();
	server.decorate("projectConfig", projectConfig);

	const knex = await initKnex(projectConfig);
	server.decorate("knex", knex);

	const createConfiggedRedis = () => {
		return createRedisConnection(projectConfig);
	};
	const redis = await initRedis(projectConfig);
	server.decorate("redis", redis);

	const redisRtConfigSub = await initRuntimeConfig(
		createConfiggedRedis,
		redis,
		server.log
	);

	initApiKey(server);

	initCookies(server, {
		cookieSignatureKey: projectConfig.cookieSignatureKey,
		cookieSignatureKeyOld: projectConfig.cookieSignatureKeyOld,
	});

	initExtRequest(server);

	initErrorHandlers(server);

	initDevApplicationCode(redis);

	routeList.forEach(
		<BodyT extends TSchema, ResponseT extends TSchema>(
			routeOptions: FastackStarterRouteOptions<BodyT, ResponseT>
		) => {
			const routeConfig = wrapRoute(routeOptions);
			if (!routeConfig) {
				return;
			} else {
				server.route(routeConfig);
			}
		}
	);

	server.register(cors, {
		origin: [
			`${process.env.FASTIFY_BASE_URL}`,
			`${process.env.NEXTJS_BASE_URL}`,
		],
		methods: ["GET", "POST", "PUT", "DELETE"],
		allowedHeaders: ["Content-Type", "Authorization", "x-api-key"],
		credentials: true,
	});

	server.addHook("onClose", async () => {
		await redis.quit();
		await redisRtConfigSub.quit();
	});

	server.listen(
		{port: projectConfig.port, host: projectConfig.host},
		(err, address) => {
			if (err) {
				console.error("server.listen error", err);
				return process.exit(1);
			}
			console.log("Server listening at " + address);
		}
	);
}

async function initWithTry() {
	try {
		await init();
	} catch (ex: any) {
		if (IS_DEV && !IS_DOCKER && ex && ex.code === "NO_REDIS") {
			console.error(ex.message);
			console.error(
				"If this is a local development server, then you may " +
					"have forgotten to run 'docker compose up -d' first."
			);
		} else {
			console.error("Error thrown on startup", "-", ex);
		}
		process.exit(1);
	}
}

// TODO: sigint handler? what will staging/prod do?

process.on("unhandledRejection", (err) => {
	console.error("unhandledRejection", err);
	process.exit(1);
});

initWithTry();
