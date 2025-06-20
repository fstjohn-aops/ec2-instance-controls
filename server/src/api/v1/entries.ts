import _ from "lodash";
import {Type} from "@sinclair/typebox";
import {
	FastackRouteInput,
	FastackStarterRouteOptions,
	FastackStarterRouteDocs,
} from "../../init/RouteWrap";
import {getEntries} from "../../dbal/entries";
import {entriesResponseT} from "../../shared/Entries";
import {camelCaseEntries} from "../../DbCamelCaser";
import {
	RequestError,
	ServerError,
	booleanT,
	toBoolean,
} from "@aops-trove/fast-server-common";

const docs: FastackStarterRouteDocs = {
	summary: "Get entries",
	description: "Gets all entries from the database",
	bodyDescriptions: {
		throwRequestError: "If true, throw a 400 error",
		throwServerError: "If true, throw a 500 error",
	},
	errors: {
		400: ["E_EXAMPLE_REQUEST_ERROR"],
		500: ["E_EXAMPLE_SERVER_ERROR"],
	},
};

const bodyT = Type.Object({
	// GET endpoints use booleanT instead of Type.Boolean()
	throwRequestError: Type.Optional(booleanT),
	throwServerError: Type.Optional(booleanT),
});
const responseT = entriesResponseT;

const config: FastackStarterRouteOptions<typeof bodyT, typeof responseT> = {
	method: "GET",
	url: "/api/v1/entries",
	docs,
	bodyT,
	responseT,
	handler,
};

async function handler(input: FastackRouteInput<typeof bodyT>) {
	const {app, body} = input;
	const {knex} = app;

	const throwRequestError = toBoolean(body.throwRequestError);
	const throwServerError = toBoolean(body.throwServerError);

	if (throwRequestError) {
		throw new RequestError("E_EXAMPLE_REQUEST_ERROR");
	}

	if (throwServerError) {
		throw new ServerError("E_EXAMPLE_SERVER_ERROR");
	}

	const entries = await getEntries(knex);

	return {entries: entries.map(camelCaseEntries)};
}

export default config;
