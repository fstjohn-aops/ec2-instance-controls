import {createDefaultUserContext, evaluate} from "@aops-trove/fast-flags";
import {checkSession} from "./Session";
import {getIp} from "./Platform";
import {log} from "./Logger";
import {evaluate_sampleFeature} from "./EvaluateFlag";

// Mock dependencies
jest.mock("@aops-trove/fast-flags", () => ({
	evaluate: jest.fn(),
	createDefaultUserContext: jest.fn(),
	getLoggedOutId: jest.fn(),
}));

jest.mock("./Session", () => ({
	checkSession: jest.fn(),
}));

jest.mock("./Platform", () => ({
	getIp: jest.fn(),
}));

jest.mock("./Logger", () => ({
	log: jest.fn(),
}));

jest.mock("next/headers", () => ({
	headers: jest.fn(),
}));

const mockEvaluate = jest.mocked(evaluate<boolean>);
const mockCheckSession = jest.mocked(checkSession);
const mockGetIp = jest.mocked(getIp);
const mockCreateDefaultUserContext = jest.mocked(createDefaultUserContext);

describe("evaluate_sampleFeature", () => {
	const mockContext = {kind: "user", key: "user-id"}; // Sample context for testing

	beforeEach(() => {
		jest.clearAllMocks();
	});

	it("should evaluate feature with given context", async () => {
		mockEvaluate.mockResolvedValue(true); // Mocking evaluate function

		const result = await evaluate_sampleFeature(mockContext);

		expect(evaluate).toHaveBeenCalledWith({
			flagKey: "sample-feature",
			context: mockContext,
			flagDefaultValue: false,
			log,
		});
		expect(result).toBe(true);
	});

	it("should create default user context with session", async () => {
		mockCheckSession.mockResolvedValue({
			sessionId: "123",
			userId: "user-id",
			hasValidStepUp: false,
			expiresAt: "future",
		});
		mockGetIp.mockReturnValue("192.168.0.1");
		mockEvaluate.mockResolvedValue(false);
		mockCreateDefaultUserContext.mockReturnValue({
			kind: "user",
			key: "user-id",
			loggedIn: true,
			officeIp: false,
			anyOtherCustomAttributeYouWant: false,
		});

		const result = await evaluate_sampleFeature();

		expect(checkSession).toHaveBeenCalled();
		expect(getIp).toHaveBeenCalled();
		expect(evaluate).toHaveBeenCalledWith({
			flagKey: "sample-feature",
			context: {
				kind: "user",
				key: "user-id",
				loggedIn: true,
				officeIp: false,
				anyOtherCustomAttributeYouWant: false,
			},
			flagDefaultValue: false,
			log,
		});
		expect(result).toBe(false);
	});

	it("should create default user context with no session", async () => {
		const loggedOutId =
			"a9b1d2598305169aa2970614f2cf3598700482dd44d170335b6c5b43736d6ccd74e075db8a617d63e1c7a47447d59c95fdf800d32e2079dabfbd433d1db5c225";

		mockCheckSession.mockResolvedValue(null);
		mockGetIp.mockReturnValue("192.168.0.1");
		mockEvaluate.mockResolvedValue(false);
		mockCreateDefaultUserContext.mockReturnValue({
			kind: "user",
			key: loggedOutId,
			loggedIn: false,
			officeIp: false,
			anyOtherCustomAttributeYouWant: false,
		});

		const result = await evaluate_sampleFeature();

		expect(checkSession).toHaveBeenCalled();
		expect(getIp).toHaveBeenCalled();
		expect(evaluate).toHaveBeenCalledWith({
			flagKey: "sample-feature",
			context: {
				kind: "user",
				key: loggedOutId,
				loggedIn: false,
				officeIp: false,
				anyOtherCustomAttributeYouWant: false,
			},
			flagDefaultValue: false,
			log,
		});
		expect(result).toBe(false);
	});
});
