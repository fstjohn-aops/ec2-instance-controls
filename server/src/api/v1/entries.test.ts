import _ from "lodash";
import {makeMockKnex} from "../../../test/MockKnex";
import {executeRoute, makeMockRouteInput} from "../../../test/MockRouteInput";
import entries from "./entries";
import {TimeWarp} from "@aops-trove/fast-test-db";
import {expectError} from "../../../test/General";
import {RequestError, ServerError} from "@aops-trove/fast-server-common";

const uuid1 = "123e4567-e89b-12d3-a456-426614174000";
const uuid2 = "234e4567-e89b-12d3-a456-426614174000";

describe("api/v1/entries", () => {
	describe("Successes", () => {
		test("Should return an empty array if there are no entries", async () => {
			const knex = await makeMockKnex();
			const input = makeMockRouteInput({
				knex,
				body: {},
			});

			// This line freezes Date.now and related functions.
			TimeWarp.timeWarpTo2017();
			// This tells Postgres to use the frozen Date.now as its now() return.
			// Most notably, column defaults will be affected. This must be called
			// after each TimeWarp modification to propagate to the database.
			await TimeWarp.syncDbNow(knex);

			const response = await executeRoute(entries, input);
			expect(response).toEqual({entries: []});
		});
		test("Should return a single entry", async () => {
			const knex = await makeMockKnex();
			const input = makeMockRouteInput({
				knex,
				body: {},
			});

			TimeWarp.timeWarpTo2017();
			await TimeWarp.syncDbNow(knex);

			await knex("entries").insert({
				id: uuid1,
				entry: "test1",
			});

			const response = await executeRoute(entries, input);
			expect(response).toEqual({
				entries: [
					{
						id: uuid1,
						entry: "test1",
						createdAt: new Date(),
						updatedAt: new Date(),
						deletedAt: null,
					},
				],
			});
		});
		test("Should return multiple entries", async () => {
			const knex = await makeMockKnex();
			const input = makeMockRouteInput({
				knex,
				body: {},
			});

			TimeWarp.timeWarpTo2017();
			await TimeWarp.syncDbNow(knex);

			await knex("entries").insert([
				{
					id: uuid1,
					entry: "test1",
				},
				{
					id: uuid2,
					entry: "test2",
				},
			]);

			const response = await executeRoute(entries, input);
			// Since the order of the response is not guaranteed, we sort by id.
			// Without sorting, the test would fail randomly.
			expect(_.sortBy(response.entries, "id")).toEqual([
				{
					id: uuid1,
					entry: "test1",
					createdAt: new Date(),
					updatedAt: new Date(),
					deletedAt: null,
				},
				{
					id: uuid2,
					entry: "test2",
					createdAt: new Date(),
					updatedAt: new Date(),
					deletedAt: null,
				},
			]);
		});
	});
	describe("Errors", () => {
		test("Should throw E_EXAMPLE_REQUEST_ERROR if throwRequestError is true", async () => {
			const knex = await makeMockKnex();
			const input = makeMockRouteInput({
				knex,
				body: {throwRequestError: "true"},
			});
			const err = await expectError(executeRoute(entries, input));
			expect(err).toBeInstanceOf(RequestError);
			expect(err.code).toEqual("E_EXAMPLE_REQUEST_ERROR");
			expect(err.status).toEqual(400);
		});
		test("Should throw E_EXAMPLE_SERVER_ERROR if throwServerError is true", async () => {
			const knex = await makeMockKnex();
			const input = makeMockRouteInput({
				knex,
				body: {throwServerError: "true"},
			});
			const err = await expectError(executeRoute(entries, input));
			expect(err).toBeInstanceOf(ServerError);
			expect(err.code).toEqual("E_EXAMPLE_SERVER_ERROR");
			expect(err.status).toEqual(500);
		});
	});
});
