/**
 * Provides a mocked version of the data in config.yaml, which the server
 * passes around as projectConfig.
 */

import _ from "lodash";
import {ProjectConfig} from "../src/init/ProjectConfig";

// Reexport for convenience
export {ProjectConfig};

const defaultMock: ProjectConfig = {
	dev: {},
	host: "127.0.0.1",
	port: 13031,
	db: {}, // Normally not empty, but tests shouldn't care.
	serverDb: "development", // Not a key in db, but tests shouldn't care.
	redisHost: "ioredis-mock",
	redisPort: 13540,
	redisDb: 0,
	apiKey: "fakeplatformapikey",
	cookieSignatureKey: "fakecookiesignaturekey",
	cookieSignatureKeyOld: "fakecookiesignaturekeyold",
	applicationCode: "fastackstarter-test",
	baseUrl: "http://127.0.0.1:13031",
	platform: {
		url: "https://faketesturl.gateway.aopspldev.com",
		loginDomain: "https://faketesturl.login.aopspldev.com",
		apiKey: "fakeplatformapikey",
	},
	aops: {
		url: "https://faketesturl.aops.org",
		api: {
			key: "fakeaopsapikey",
			email: "fakeaopsemail",
		},
		htaccess: {
			user: "fakeaopshtaccessuser",
			password: "fakeaopshtaccesspassword",
		},
	},
};

/**
 * Return a fake config. All required fields that matter have defaults, but
 * you can pass an override for anything in the arguments.
 */
export function makeMockProjectConfig(
	overrides?: Partial<ProjectConfig>
): ProjectConfig {
	return _.extend({}, defaultMock, overrides || {});
}
