// @ts-check

// Start with a strict ContentSecurity Policy and expand as needed.
// See: https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP#writing_a_policy
const cspHeader = `
	default-src 'self';
	connect-src 'self' ${process.env.NEXT_PUBLIC_FASTIFY_BASE_URL};
	script-src 'self' 'unsafe-inline' ${process.env.NODE_ENV === "production" ? "" : "'unsafe-eval'"};
	style-src 'self' 'unsafe-inline';
	img-src 'self' blob: data:;
	font-src 'self';
	object-src 'none';
	base-uri 'self';
	form-action 'self';
	frame-ancestors 'none';
	block-all-mixed-content;
	upgrade-insecure-requests;
`;

/** @type {import('next').NextConfig} */
const nextConfig = {
	experimental: {
		serverComponentsExternalPackages: ["pino", "pino-pretty"],
	},
	async headers() {
		return [
			{
				source: "/(.*)",
				headers: [
					{
						key: "Content-Security-Policy",
						value: cspHeader.replace(/\n/g, ""),
					},
				],
			},
		];
	},
};

export default nextConfig;
