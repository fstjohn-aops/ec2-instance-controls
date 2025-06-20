import _ from "lodash";
import {FastifyInstance, FastifyRequest, FastifyReply} from "fastify";
import {
	RequestError,
	ServerError,
	makeLoggableError,
} from "@aops-trove/fast-server-common";

export function initErrorHandlers(server: FastifyInstance) {
	server.setErrorHandler(function (
		error: any,
		request: FastifyRequest,
		reply: FastifyReply
	) {
		let code: string;
		let status: number;
		let message: string;
		let moreInfo: any;
		if (error instanceof RequestError) {
			code = error.code;
			message = error.message;
			status = error.status;
			moreInfo = error.moreInfo;
			request.log.warn(
				{module: "ServerErrors", code, message, status, moreInfo},
				"RequestError"
			);
		} else if (error instanceof ServerError) {
			code = error.code;
			message = error.message;
			status = error.status;
			moreInfo = error.moreInfo;
			request.log.error({code, message, status, moreInfo}, "ServerError");
		} else {
			error = error || {};
			code = "E_UNKNOWN";
			message = error.message || "Unexpected error occurred";
			if (error.code) {
				message += " (" + error.code + ")";
			}
			status = error.status >= 400 ? error.status : 500;
			request.log.error(
				{
					module: "ServerErrors",
					code,
					message,
					status,
					original: makeLoggableError(error),
				},
				"Unexpected error"
			);
		}
		reply
			.status(status)
			.header("Content-Type", "application/json; charset=utf-8")
			.send({
				code,
				message,
				moreInfo,
			});
	});

	server.setNotFoundHandler(function (
		request: FastifyRequest,
		reply: FastifyReply
	) {
		const badPath = request.method + " " + request.url;
		const moreInfo = {method: request.method, path: request.url, status: 404};
		request.log.warn({module: "ServerErrors", ...moreInfo}, "404");
		reply
			.status(404)
			.header("Content-Type", "application/json; charset=utf-8")
			.send({
				code: "E_NOT_FOUND",
				message: badPath + " not found",
				moreInfo,
			});
	});
}
