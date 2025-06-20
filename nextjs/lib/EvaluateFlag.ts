import {
	ContextCustomAttributes,
	LDContext,
	createDefaultUserContext,
	evaluate,
	getLoggedOutId,
} from "@aops-trove/fast-flags";
import {headers} from "next/headers";
import {checkSession} from "./Session";
import {getIp} from "./Platform";
import {log} from "./Logger";
import {isOfficeIp} from "./isOfficeIp";

/**
 * Evaluate the `sample-feature` flag, which defaults to false.
 */
export async function evaluate_sampleFeature(passedContext?: LDContext) {
	const flagDefaultValue = false;

	const context = passedContext ? passedContext : await makeDefaultContext();
	const result = await evaluate({
		flagKey: "sample-feature",
		context,
		flagDefaultValue,
		log,
	});
	return result;
}

async function makeDefaultContext() {
	const session = await checkSession();

	const ip = getIp(headers());
	const identifier = session ?? getLoggedOutId(ip);

	const officeIp = isOfficeIp(ip);
	const defaultCustomAttributes: ContextCustomAttributes = {
		officeIp,
		anyOtherCustomAttributeYouWant: false,
	};

	const context = createDefaultUserContext(identifier, defaultCustomAttributes);
	return context;
}
