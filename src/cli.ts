#!/usr/bin/env node
import { defaultSettings, type Settings } from "./config.js";
import { DocumentConverter } from "./ingestion/converter.js";
import { IndexBuilder } from "./ingestion/indexBuilder.js";
import { KnowFlowWorkflow } from "./workflow.js";

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  const command = args.shift();
  if (command === "ingest") {
    const rawDir = option(args, "--raw-dir", defaultSettings.rawDir);
    const markdownDir = option(args, "--markdown-dir", defaultSettings.markdownDir);
    const kbDir = option(args, "--kb-dir", defaultSettings.knowledgeBaseDir);
    const converter = new DocumentConverter();
    const markdownFiles = await converter.convertDirectory(rawDir, markdownDir);
    const manifest = await new IndexBuilder(kbDir).buildFromMarkdown(markdownDir);
    console.log(`Converted ${markdownFiles.length} files and indexed ${manifest.documents.length} documents.`);
    return;
  }
  if (command === "ask") {
    const json = args.includes("--json");
    const kbDir = option(args, "--kb-dir", defaultSettings.knowledgeBaseDir);
    const query = positional(args).join(" ");
    if (!query) throw new Error("Missing query.");
    const settings: Settings = { ...defaultSettings, knowledgeBaseDir: kbDir };
    const answer = await new KnowFlowWorkflow(settings).answerQuery(query);
    if (json) console.log(JSON.stringify(answer, null, 2));
    else {
      console.log(answer.answer);
      console.log(`\nConfidence: ${answer.confidence.toFixed(2)}`);
    }
    return;
  }
  console.error("Usage: knowflow <ingest|ask> [options]");
  process.exitCode = 2;
}

function option(args: string[], name: string, fallback: string): string {
  const idx = args.indexOf(name);
  return idx >= 0 ? args[idx + 1] ?? fallback : fallback;
}

function positional(args: string[]): string[] {
  const values: string[] = [];
  for (let idx = 0; idx < args.length; idx += 1) {
    const arg = args[idx];
    if (!arg || arg === "--json") continue;
    if (arg.startsWith("--")) {
      idx += 1;
      continue;
    }
    values.push(arg);
  }
  return values;
}

main().catch((error: unknown) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exitCode = 1;
});
