/**
 * Small file with per-test-file setup. Used as setupFilesAfterEnv in
 * jest.config.js.
 */

import {TimeWarp} from "@aops-trove/fast-test-db";
TimeWarp.setupJestHooks();
