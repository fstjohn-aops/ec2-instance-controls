import "./ExampleButton.scss";

interface ButtonProps {
	/**
	 * Is this the principal call to action on the page?
	 */
	primary?: boolean;
	/**
	 * What background color to use
	 */
	backgroundColor?: string;
	/**
	 * How large should the button be?
	 */
	size?: "small" | "medium" | "large";
	/**
	 * Button contents
	 */
	label: string;
	/**
	 * Optional click handler
	 */
	onClick?: () => void;
}

/**
 * Primary UI component for user interaction
 */
export const ExampleButton = ({
	primary = false,
	size = "medium",
	backgroundColor,
	label,
	...props
}: ButtonProps) => {
	const mode = primary
		? "storybook-example-button--primary"
		: "storybook-example-button--secondary";
	return (
		<button
			type="button"
			className={[
				"storybook-example-button",
				`storybook-example-button--${size}`,
				mode,
			].join(" ")}
			{...props}
		>
			{label}
			<style jsx>{`
				button {
					background-color: ${backgroundColor};
				}
			`}</style>
		</button>
	);
};
