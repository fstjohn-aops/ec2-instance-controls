import Link from "next/link";
import styles from "./page.module.scss";
import {checkSession, getSignInUrl, getSignOutUrl} from "@/lib/Session";
import {evaluate_sampleFeature} from "../lib/EvaluateFlag";

export default async function Home() {
	const session = await checkSession();
	const enabled = await evaluate_sampleFeature();

	return (
		<main className={styles.main}>
			<p>
				This is served by the Next.js App Router which uses{" "}
				<a
					target="_blank"
					href="https://nextjs.org/docs/app/building-your-application/routing"
				>
					file-based routing
				</a>{" "}
				and introduces{" "}
				<a
					target="_blank"
					href="https://nextjs.org/docs/app/building-your-application/rendering"
				>
					Server and Client components
				</a>
				. To see what these unlock, check the{" "}
				<a target="_blank" href="https://app-router.vercel.app/">
					App Router Example
				</a>
				.
			</p>
			<p>
				Try visiting the login-protected{" "}
				<Link href="/dashboard">Dashboard</Link>.
			</p>
			<p>
				The feature flag{" "}
				<Link
					target="_blank"
					href="https://app.launchdarkly.com/projects/default/flags/sample-feature/targeting?env=test&selected-env=test"
				>
					sample-feature
				</Link>{" "}
				is {enabled ? "on" : "off"}.{" "}
				{session
					? ""
					: "Try logging in to see if the value is different for logged-in users."}
			</p>
			{!session && <a href={getSignInUrl()}>Sign in</a>}
			{session && <a href={getSignOutUrl()}>Sign out</a>}
		</main>
	);
}
