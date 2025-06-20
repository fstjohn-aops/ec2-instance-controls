import _ from "lodash";
import {Knex} from "knex";
import {Redis} from "ioredis";
import {
	FastifyRequest,
	FastifyReply,
	RouteOptions,
	FastifyContextConfig,
} from "fastify";
import {Static, TSchema} from "@sinclair/typebox";

import {IS_DEV} from "../util/General";
import {ExtRequestFunc} from "@aops-trove/fast-ext-request";
import {ProjectConfig} from "./ProjectConfig";
import {
	RequestError,
	ServerError,
	LogApi,
	checkTypebox,
	isMethodDisallowingBody,
	replyStatus,
	replySetCorsHeader,
	replyRedirect,
} from "@aops-trove/fast-server-common";
import {CookieApi, createCookieApi} from "@aops-trove/fast-cookie";
import {initPlaccSdk, PlaccSdkObject} from "@aops-trove/placc-sdk";
import {getDevApplicationCode} from "./DevApplicationCode";

// 100 * 1024 * 1024 = 100MB
const LARGE_PAYLOAD_BYTE_LIMIT = 100 * 1024 * 1024;

/**
 * Shape of the route config exported by each src/api file. The wrapRoute
 * function converts it to what Fastify natively expects.
 */
export type FastackStarterRouteOptions<
	BodyT extends TSchema,
	ResponseT extends TSchema,
> = {
	/**
	 * HTTP method, like "GET" or "POST". (The type could be more specific, but
	 * non-TS route files will infer it as a string.)
	 */
	method: string;
	/**
	 * Route path.
	 */
	url: string;
	/**
	 * Main handler.
	 */
	handler: (input: FastackRouteInput<BodyT>) => Promise<Static<ResponseT>>;
	/**
	 * If true, allow very large payloads up to LARGE_PAYLOAD_BYTE_LIMIT above.
	 * (If false, use the server's limit. Fastify's default is 1MB.)
	 */
	allowLargeBody?: boolean;
	/**
	 * Optional. If true, exclude this route in production.
	 */
	devOnly?: boolean;
	/**
	 * Optional. If provided, will set custom config on route.
	 */
	config?: FastifyContextConfig;
	/**
	 * Typebox value. If set, check the payload against this schema and
	 * 400 without calling the handler if the check fails. Also used in
	 * documentation.
	 */
	bodyT: BodyT;
	/**
	 * Typebox value. If set, check the response against this schema
	 * and log violations (but never interfere with the response). Also used in
	 * documentation.
	 */
	responseT: ResponseT;
	/**
	 * Object with documentation info.
	 */
	docs: FastackStarterRouteDocs;
};

export type FastackStarterRouteDocs = {
	/**
	 * Quick summary of endpoint, used in documentation.
	 * Appears in headers and the table of contents, so be concise and direct.
	 */
	summary: string;
	/**
	 * Full description of endpoint, used in documentation.
	 */
	description: string;
	/**
	 * Description of each body field, used in documentation.
	 * Should match the fields on bodyT.
	 */
	bodyDescriptions: {[name: string]: string};
	errors: {[statusCode: string]: string[]};
};

/**
 * Info about the client making the request.
 */
export type ClientInfo = {
	ip: string;
	userAgent: string;
	cookieApi: CookieApi;
};

export type FastackStarterBaseInput<Body> = {
	body: Body;
	log: LogApi;

	/**
	 * Info about the environment the server is running in.
	 */
	env: {
		dev: boolean;
		projectConfig: ProjectConfig;
	};
	/**
	 * Services available to server routes, like database connections.
	 */
	app: {
		knex: Knex;
		redis: Redis;
		extRequest: ExtRequestFunc;
		placcSdk: PlaccSdkObject;
	};
};

/**
 * Object passed as a parameter to each route handler.
 */
export type FastackRouteInput<BodyT extends TSchema> = FastackStarterBaseInput<
	Static<BodyT>
> & {
	requestId: string;
	method: string;
	url: string;
	params: any;
	query: any;
	baseUrl: string;
	client: ClientInfo;
	// @TODO: add perms eventually
	/**
	 * Reply helper. If you return an ordinary JS value, it means a JSON response with status 200.
	 */
	replyStatus: (status: number, body: string | object) => void;
	/**
	 * Call this when other sites should be able to access the route you are
	 * defining with CORS. (You don't need this when themis needs other things
	 * with CORS.)
	 */
	replySetCorsHeader: (reply: FastifyReply) => void;
	replyRedirect: (url: string) => void;
};

export function wrapRoute<BodyT extends TSchema, ResponseT extends TSchema>(
	routeOptions: FastackStarterRouteOptions<BodyT, ResponseT>
): RouteOptions | null {
	if (routeOptions.devOnly && !IS_DEV) {
		return null;
	}
	const {bodyT, responseT} = routeOptions;

	async function handler(request: FastifyRequest, reply: FastifyReply) {
		const input = await makeRouteInput(request, reply);

		if (bodyT) {
			try {
				checkTypebox({
					schema: bodyT,
					value: input.body,
					errorPrefix: input.url + " body",
					log: input.log,
				});
			} catch (ex: any) {
				throw new RequestError("E_INVALID_PARAMETERS", {
					moreInfo: {errorMessage: ex.message},
				});
			}
		}

		const res = await routeOptions.handler(input);

		if (responseT) {
			try {
				checkTypebox({
					schema: responseT,
					value: res,
					errorPrefix: input.url + " response",
					log: input.log,
				});
			} catch (ex: any) {
				input.log.error({
					module: "RouteWrap",
					method: input.method,
					url: input.url,
					step: "response typecheck",
					fullError: ex.message,
				});

				if (IS_DEV) {
					throw new ServerError("E_INVALID_RESPONSE", {
						moreInfo: {
							originalResponse: res,
							responseT,
							errorMessage: ex.message,
						},
					});
				}
			}
		}

		return res;
	}

	const routeConfig: RouteOptions = {
		method: routeOptions.method as any,
		url: routeOptions.url,
		handler,
		config: routeOptions.config || {
			// Used by src/init/ApiKey
			requireApiKey: true,
		},
	};
	if (routeOptions.allowLargeBody) {
		routeConfig.bodyLimit = LARGE_PAYLOAD_BYTE_LIMIT;
	}
	return routeConfig;
}

export async function makeRouteInput(
	request: FastifyRequest,
	reply: FastifyReply
): Promise<FastackRouteInput<any>> {
	let body: any = request.body;
	if (isMethodDisallowingBody(request.method)) {
		body = request.query;
	}

	const ip = request.ip;
	const userAgent = _.get(request.headers, "user-agent", "");

	const placcSdk = initPlaccSdk({
		baseUrl: request.server.projectConfig.platform.url,
		apiKey: request.server.projectConfig.platform.apiKey,
		extRequest: request.extRequest,
		redis: request.server.redis,
		log: request.log,
		agent: {
			applicationCode: request.server.projectConfig.applicationCode,
			devApplicationCode: await getDevApplicationCode(request.server.redis),
			ip,
			userAgent,
		},
		//These are optional parameters, configure as needed. These are best guesses at defaults.
		checkBodyType: {
			throwErrorOnFail: IS_DEV,
			logLevelOnFail: "error",
		},
		checkResponseType: {
			throwErrorOnFail: IS_DEV,
			logLevelOnFail: "error",
		},
	});

	return {
		requestId: request.id,
		method: request.method,
		baseUrl: request.server.projectConfig.baseUrl,
		url: request.url,
		params: request.params as any,
		query: request.query as any,
		body,
		log: request.log,
		env: {
			dev: IS_DEV,
			projectConfig: request.server.projectConfig,
		},
		app: {
			knex: request.server.knex,
			redis: request.server.redis,
			extRequest: request.extRequest,
			placcSdk,
		},
		client: {
			ip,
			userAgent,
			cookieApi: createCookieApi(request, reply, {isDev: IS_DEV}),
		},
		replyStatus: (status, replyBody) =>
			replyStatus(request, reply, status, replyBody),
		replySetCorsHeader: () => replySetCorsHeader(reply),
		replyRedirect: (url) => replyRedirect(request, reply, url),
	};
}
