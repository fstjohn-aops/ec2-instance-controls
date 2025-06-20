import type {StorybookConfig} from "@storybook/nextjs";

const config: StorybookConfig = {
	stories: ["../**/*.stories.@(js|jsx|mjs|ts|tsx)"],
	addons: ["@storybook/addon-links", "@storybook/addon-essentials"],
	framework: {
		name: "@storybook/nextjs",
		options: {},
	},
	docs: {},
	staticDirs: ["../public"],
	typescript: {
		check: true,
		reactDocgen: "react-docgen-typescript",
	},
};
export default config;
