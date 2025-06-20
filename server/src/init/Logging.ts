import {FastifyInstance, FastifyServerOptions} from "fastify";
import Os from "os";
import _ from "lodash";
import {LoggerOptions as PinoLoggerOptions} from "pino";
import {IS_DEV} from "../util/General";

const MAX_STRING_RESPONSE_SIZE_TO_LOG = 200;
const MAX_ARRAY_SIZE_TO_LOG = 10;

const FIELDS_TO_REDACT = [
	"body.password",
	"body.user.password",
	"body.update.password",
	"body.currentPassword",
	"body.users[*].password",
	"headers['X-Auth-Key']",
	"headers['X-Auth-Email']",
	"headers['x-api-key']",
	"headers.Authorization",
];

export type LoggingConfig = Partial<FastifyServerOptions> & {
	logger?: PinoLoggerOptions;
};
export function getLoggingConfig(): LoggingConfig {
	const logBase = {
		pid: process.pid,
		hostname: Os.hostname(),
	};
	const level = IS_DEV || process.env.LOG_DEBUG ? "debug" : "info";

	return {
		logger: IS_DEV
			? {
					redact: FIELDS_TO_REDACT,
					level,
					transport: {
						target: "pino-pretty",
					},
					base: logBase,
				}
			: ({
					redact: FIELDS_TO_REDACT,
					level,
					base: logBase,
				} as any),
		disableRequestLogging: true,
	};
}

function truncateBody(body: any) {
	if (_.isString(body)) {
		if (body.length <= MAX_STRING_RESPONSE_SIZE_TO_LOG) {
			return {info: {}, newBody: body};
		}
		const newBody = body.slice(0, MAX_STRING_RESPONSE_SIZE_TO_LOG);
		return {info: {bodyLength: body.length}, newBody};
	}

	const info: {[key: string]: number} = {};
	const newBody = _.mapValues(body, (v, k) => {
		if (_.isArray(v) && v.length > MAX_ARRAY_SIZE_TO_LOG) {
			info[k] = v.length;
			return v.slice(0, MAX_ARRAY_SIZE_TO_LOG);
		} else {
			return v;
		}
	});
	return {info, newBody};
}

function getUrlFamily(url?: string) {
	let urlFamily = url;
	if (url) {
		urlFamily = url.split("?")[0];
	}
	return urlFamily;
}

export function initRequestLogging(server: FastifyInstance) {
	server.decorateReply("payload", null);

	server.addHook("preValidation", async function (request, _reply) {
		// Log incoming requests. This is to replace fastify default logging.
		const {info, newBody} = truncateBody(request.body);
		const infoToLog: any = {
			module: "Logging",
			type: "request",
			phase: "start",
			req: request,
			urlFamily: getUrlFamily(request.url),
			body: newBody,
			query: request.query,
		};
		if (!_.isEmpty(info)) {
			infoToLog.truncatedFrom = info;
		}
		request.log.info(infoToLog, "Incoming Request");
	});

	server.addHook("onResponse", async function (request, reply) {
		// Log completed requests. This is to replace fastify default logging.
		const {info, newBody} = truncateBody(reply.payload);
		const infoToLog: any = {
			module: "Logging",
			type: "request",
			phase: "end",
			req: request,
			urlFamily: getUrlFamily(request.url),
			statusCode: reply.raw.statusCode,
			responseTime: reply.elapsedTime,
			resp: newBody,
		};
		if (!_.isEmpty(info)) {
			infoToLog.truncatedFrom = info;
		}
		request.log.info(infoToLog, "Request Completed");
	});

	server.addHook("preSerialization", async function (_request, reply, payload) {
		// Make response available for logging, without needing to JSON.parse
		// if possible.
		reply.payload = payload;
	});

	server.addHook("onSend", async function (_request, reply, payload) {
		// If preSerialization didn't add anything, try again.
		if (!reply.payload && payload && typeof payload === "string") {
			reply.payload = payload;
		}
	});
}
