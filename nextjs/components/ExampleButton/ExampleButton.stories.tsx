import type {Meta, StoryObj} from "@storybook/react";
import {ExampleButton} from "./ExampleButton";

// More on how to set up stories at: https://storybook.js.org/docs/writing-stories#default-export
const meta: Meta<typeof ExampleButton> = {
	title: "components/ExampleButton",
	component: ExampleButton,
	parameters: {
		// Optional parameter to center the component in the Canvas. More info: https://storybook.js.org/docs/configure/story-layout
		layout: "centered",
	},
	// More on argTypes: https://storybook.js.org/docs/api/argtypes
	argTypes: {
		backgroundColor: {control: "color"},
	},
} satisfies Meta<typeof ExampleButton>;

export default meta;
type ExampleButtonStory = StoryObj<typeof meta>;

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Primary: ExampleButtonStory = {
	args: {
		primary: true,
		label: "Button",
	},
};

export const Secondary: ExampleButtonStory = {
	args: {
		label: "Button",
	},
};

export const Large: ExampleButtonStory = {
	args: {
		size: "large",
		label: "Button",
	},
};

export const Small: ExampleButtonStory = {
	args: {
		size: "small",
		label: "Button",
	},
};

export const Warning: ExampleButtonStory = {
	args: {
		primary: true,
		label: "Delete now",
		backgroundColor: "red",
	},
};
