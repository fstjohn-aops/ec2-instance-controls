/**
 * Checks if an IP address belongs to the office.
 */
export function isOfficeIp(ip: string) {
	return [
		"50.203.25.222", // Office IP address
		"98.152.34.74", // Office IP backup address
	].includes(ip);
}
