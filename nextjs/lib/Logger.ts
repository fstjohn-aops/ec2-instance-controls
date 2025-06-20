import type {LogApi} from "@aops-trove/fast-server-common";
import pino from "pino";
import {IS_DEV} from "./General";

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

export const log: LogApi = IS_DEV
	? // Pretty print in development
		pino({
			transport: {
				target: "pino-pretty",
				options: {
					colorize: true,
				},
			},
			level: "debug",
			redact: FIELDS_TO_REDACT,
		})
	: // JSON in production
		pino({level: "info", redact: FIELDS_TO_REDACT});
