/**
 * NOTE: CODEGEN IS USED IN THIS FILE. Careless manual edits may be lost.
 *
 * This file bulk imports everything in src/api, which has all of the API
 * endpoints.
 *
 * Run `npx tsx tools/genBulkImports.ts` to update the codegen'd portion.
 * Everything between @@ BEGIN BULKIMPORT and @@ END BULKIMPORT is controlled
 * by this script, and the original body is discarded.
 */
import {FastackStarterRouteOptions} from "./RouteWrap";

//@@ dir = src/api
//@@ exclude = *.test.ts
//@@ type = FastackStarterRouteOptions<any, any>
//@@ varName = routeList
//@@ BEGIN BULKIMPORT
import Src_Api_V1_Entries from "../api/v1/entries";

const routeList: FastackStarterRouteOptions<any, any>[] = [Src_Api_V1_Entries];
//@@ END BULKIMPORT

export default routeList;
