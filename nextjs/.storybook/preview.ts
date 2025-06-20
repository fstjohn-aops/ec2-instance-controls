import type {Preview} from "@storybook/react";
import "../app/global.scss";

const preview: Preview = {
	parameters: {
		controls: {
			expanded: true,
		},
	},
	tags: ["autodocs"],
};

export default preview;
