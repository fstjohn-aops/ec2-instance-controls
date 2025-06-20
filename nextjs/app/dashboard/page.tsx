import Link from "next/link";
import styles from "../page.module.scss";
import {checkSessionOrRedirect} from "@/lib/Session";
import {getEntries} from "@/lib/getEntries";
import {evaluate_sampleFeature} from "../../lib/EvaluateFlag";
import {getPlaccSdk} from "@/lib/Platform";

export default async function Dashboard() {
	const session = await checkSessionOrRedirect();
	const entries = await getEntries();

	const enabled = await evaluate_sampleFeature();

	const placcSdk = await getPlaccSdk({
		sessionId: session.sessionId,
		userId: session.userId,
	});
	const userRet = await placcSdk.getUser({userId: session.userId});
	const user = userRet?.user;

	return (
		<main className={styles.main}>
			<Link href="./">Back to home</Link>
			<p>`sample-feature` flag is {enabled ? "on" : "off"}</p>
			{user && <p>Welcome back, {user.email}.</p>}
			<h3>Database entries</h3>
			{JSON.stringify(entries)}
			{session && (
				<>
					<h3>Session</h3>
					<ul>
						{Object.keys(session).map((k) => (
							<li key={`session-info-${k}`}>
								{k} : {JSON.stringify(session?.[k as keyof typeof session])}
							</li>
						))}
					</ul>
				</>
			)}
			{user && (
				<>
					<h3>User</h3>
					<ul>
						{Object.keys(userRet).map((k) => (
							<li key={`user-info-${k}`}>
								{k} : {JSON.stringify(userRet?.[k as keyof typeof userRet])}
							</li>
						))}
					</ul>
				</>
			)}
		</main>
	);
}
