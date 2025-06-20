/**
 * Utility for generating fake FastackStarterRouteInput values suitable to pass to real
 * routes and run tests with.
 */

import _ from "lodash";
import {Knex} from "knex";
import {Redis} from "ioredis";
import {TSchema, Static} from "@sinclair/typebox";

import {makeMockRedis} from "./MockRedis";
import {
	MockLog,
	makeBaseMockRouteInput,
} from "@aops-trove/fast-server-common/src/testing";
import {ProjectConfig, makeMockProjectConfig} from "./MockProjectConfig";
import {MockExtRequest, makeMockExtRequest} from "./MockExtRequest";
import {checkTypebox} from "@aops-trove/fast-server-common";
import {
	FastackRouteInput,
	FastackStarterRouteOptions,
} from "../src/init/RouteWrap";
import {makeMockPlaccSdk, MockPlaccSdkObject} from "@aops-trove/placc-sdk";

export type InputProps = {
	knex: Knex;

	redis?: Redis;
	mockLog?: MockLog;
	mockExtRequest?: MockExtRequest;
	placcSdk?: MockPlaccSdkObject;

	routeConfig?: FastackStarterRouteOptions<any, any>;
	method?: string;
	url?: string;
	params?: any;
	query?: any;
	body?: any;

	notDev?: boolean;
	projectConfig?: ProjectConfig;
};

export type ExecuteOptions = {
	/**
	 * If the route config provides a bodyT, executeRoute will run checkTypebox
	 * against the passed body. Pass true here to skip that.
	 */
	skipBodyCheck?: boolean;
	/**
	 * If the route config provides a responseT, executeRoute will run
	 * checkTypebox against the computed response. Pass true here to skip that.
	 */
	skipResponseCheck?: boolean;
};

/**
 * Helper for executing a route given its config and the input from
 * makeMockRouteInput. A thin wrapper around routeOptions.handler(input) that
 * also does some type checking.
 *
 * The third options parameter, which can be omitted, can control whether these
 * checks happen; see the ExecuteOptions type above for details.
 */
export async function executeRoute<TIn extends TSchema, TOut extends TSchema>(
	routeOptions: FastackStarterRouteOptions<TIn, TOut>,
	input: FastackRouteInput<TIn>,
	execOptions: ExecuteOptions = {}
): Promise<Static<TOut>> {
	if (routeOptions.bodyT && !execOptions.skipBodyCheck) {
		checkTypebox({
			schema: routeOptions.bodyT,
			value: input.body,
			errorPrefix: input.url + " body",
			log: input.log,
		});
	}

	const response = await routeOptions.handler(input);

	if (routeOptions.responseT && !execOptions.skipResponseCheck) {
		checkTypebox({
			schema: routeOptions.responseT,
			value: response,
			errorPrefix: input.url + " response",
			log: input.log,
		});
	}

	return response;
}

/**
 * Create a mock route input value that the server expects in route handlers.
 *
 * The only required field in the argument is a knex connection, which can be
 * obtained from MockKnex. Other necessary fields, like Redis, will be filled
 * with a usable default, often drawing on other files implementing mocks.
 *
 * Be careful calling this multiple times in one test. Unless you pass in
 * shared instances yourself, things like the Redis mock will be created
 * separately and not share data. You should use makeAltInput instead, which is
 * designed for this sort of use.
 */
export function makeMockRouteInput(
	props: InputProps
): FastackRouteInput<any> & {app: {placcSdk: MockPlaccSdkObject}} {
	const redis: Redis = props.redis || makeMockRedis();
	const mockExtRequest: MockExtRequest =
		props.mockExtRequest || makeMockExtRequest();
	const dev = !props.notDev;
	const projectConfig = props.projectConfig || makeMockProjectConfig();

	const baseRouteInput = makeBaseMockRouteInput(props);
	const placcSdk =
		props.placcSdk ||
		makeMockPlaccSdk({
			baseUrl: projectConfig.platform.url,
			apiKey: projectConfig.platform.apiKey,
			agent: {
				applicationCode: projectConfig.applicationCode,
				devApplicationCode: "fastackstarter-jest",
				ip: "127.0.0.1",
				userAgent: "test-user-agent",
			},
			redis,
			log: baseRouteInput.log,
			//These are optional parameters, configure as needed. These are best guesses at defaults.
			checkBodyType: {
				throwErrorOnFail: dev,
				logLevelOnFail: "error",
			},
		});

	return {
		...baseRouteInput,
		baseUrl: projectConfig.baseUrl,
		env: {
			dev,
			projectConfig,
		},
		app: {
			knex: props.knex,
			redis,
			extRequest: mockExtRequest.fn,
			placcSdk,
		},
		replyStatus: jest.fn(),
		replySetCorsHeader: jest.fn(),
		replyRedirect: jest.fn(),
		client: {
			ip: "127.0.0.1",
			userAgent: "test-user-agent",
			// TODO: full cookie mock?
			cookieApi: {
				get: jest.fn(),
				set: jest.fn(),
				clear: jest.fn(),
				readonly: false,
			},
		},
	};
}

/**
 * Create an input value based on another one with slight differences. The
 * second parameter expects the same shape as makeMockRouteInput except no
 * fields are required,
 *
 * If you want multiple route input values in a test that have slight
 * differences, create the first one with makeMockRouteInput and all subsequent
 * ones using this function. It will ensure that things like the Redis data
 * that should be shared are shared.
 */
export function makeAltInput(
	input: FastackRouteInput<any>,
	props: Partial<InputProps>
): FastackRouteInput<any> {
	const realProps: InputProps = _.extend(
		{
			knex: input.app.knex,
			redis: input.app.redis,
		},
		props
	);
	return makeMockRouteInput(realProps);
}
