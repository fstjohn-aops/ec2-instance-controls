const {defaults} = require("jest-config");

module.exports = {
	testPathIgnorePatterns: [...defaults.testPathIgnorePatterns, "tsout"],
	globalSetup: "./test/TestStartup.ts",
	setupFilesAfterEnv: ["./test/SetupAfterEnv.ts"],
};
