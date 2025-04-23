/// <reference types="./global.d.ts" />

import { z } from "zod";
import * as fs from "node:fs/promises";
import * as path from "node:path";
import {
  GraphSchema,
  resolveGraph,
  runGraphSchemaWorker,
} from "./src/graph.mts";
import { build } from "@langchain/langgraph-ui";
import { filterValidExportPath } from "./src/utils/files.mts";

const __dirname = new URL(".", import.meta.url).pathname;

async function main() {
  const specs = Object.entries(
    z.record(z.string()).parse(JSON.parse(process.env.LANGSERVE_GRAPHS))
  ).filter(([_, spec]) => filterValidExportPath(spec));

  const GRAPH_SCHEMAS: Record<string, Record<string, GraphSchema> | false> = {};
  let failed = false;

  try {
    await Promise.all(
      specs.map(async ([graphId, rawSpec]) => {
        console.info(`[${graphId}]: Checking for source file existence`);
        const { resolved, ...spec } = await resolveGraph(rawSpec, {
          onlyFilePresence: true,
        });

        try {
          console.info(`[${graphId}]: Extracting schema`);
          GRAPH_SCHEMAS[graphId] = await runGraphSchemaWorker(spec, {
            timeoutMs: 120_000,
          });
        } catch (error) {
          console.error(`[${graphId}]: Error extracting schema: ${error}`);
          GRAPH_SCHEMAS[graphId] = false;
        }
      })
    );

    await fs.writeFile(
      path.resolve(__dirname, "client.schemas.json"),
      JSON.stringify(GRAPH_SCHEMAS),
      { encoding: "utf-8" }
    );
  } catch (error) {
    console.error(`Error resolving graphs: ${error}`);
    failed = true;
  }

  // Build Gen UI assets
  try {
    console.info("Checking for UI assets");
    await fs.mkdir(path.resolve(__dirname, "ui"), { recursive: true });

    await build({ output: path.resolve(__dirname, "ui") });
  } catch (error) {
    console.error(`Error building UI: ${error}`);
    failed = true;
  }

  if (failed) process.exit(1);
}

main();
