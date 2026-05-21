import fs from "node:fs/promises";
import path from "node:path";
import { spawn } from "node:child_process";
import fg from "fast-glob";
import { type GrepHit } from "../types.js";
import { tokenize } from "../textUtils.js";

export class GrepRetriever {
  constructor(private knowledgeBaseDir: string) {}

  async search(queries: string[], targets: string[], contextLines = 0, maxHitsPerQuery = 80): Promise<GrepHit[]> {
    const batches = await Promise.all(queries.map((query) => this.searchOne(query, targets, contextLines, maxHitsPerQuery)));
    return batches.flat();
  }

  private async searchOne(query: string, targets: string[], contextLines: number, maxHits: number): Promise<GrepHit[]> {
    const terms = tokenize(query);
    if (!terms.length) return [];
    return (await hasRg()) ? this.rg(query, terms, targets, contextLines, maxHits) : this.nodeSearch(query, terms, targets, maxHits);
  }

  private async rg(query: string, terms: string[], targets: string[], contextLines: number, maxHits: number): Promise<GrepHit[]> {
    const pattern = terms.join("|");
    const args = ["--line-number", "--ignore-case", "--no-heading", "--glob", "*.md", "-C", String(contextLines), pattern, ...targets];
    const stdout = await run("rg", args);
    const hits: GrepHit[] = [];
    for (const raw of stdout.split(/\r?\n/)) {
      const parsed = parseRgLine(raw);
      if (!parsed) continue;
      const matchedTerms = terms.filter((term) => parsed.lineText.toLowerCase().includes(term.toLowerCase()));
      if (matchedTerms.length) {
        hits.push({
          file: relativeTo(this.knowledgeBaseDir, parsed.file),
          lineNumber: parsed.lineNumber,
          lineText: parsed.lineText,
          query,
          matchedTerms
        });
      }
      if (hits.length >= maxHits) break;
    }
    return hits;
  }

  private async nodeSearch(query: string, terms: string[], targets: string[], maxHits: number): Promise<GrepHit[]> {
    const files = (await Promise.all(targets.map((target) => markdownFiles(target)))).flat();
    const hits: GrepHit[] = [];
    for (const file of files) {
      const lines = (await fs.readFile(file, "utf8")).split(/\r?\n/);
      lines.forEach((lineText, idx) => {
        const matchedTerms = terms.filter((term) => lineText.toLowerCase().includes(term.toLowerCase()));
        if (matchedTerms.length && hits.length < maxHits) {
          hits.push({ file: relativeTo(this.knowledgeBaseDir, file), lineNumber: idx + 1, lineText, query, matchedTerms });
        }
      });
      if (hits.length >= maxHits) break;
    }
    return hits;
  }
}

async function markdownFiles(target: string): Promise<string[]> {
  const stat = await fs.stat(target);
  if (stat.isFile() && target.endsWith(".md")) return [target];
  if (stat.isDirectory()) return fg("**/*.md", { cwd: target, onlyFiles: true, absolute: true });
  return [];
}

async function hasRg(): Promise<boolean> {
  try {
    await run("rg", ["--version"]);
    return true;
  } catch {
    return false;
  }
}

function run(command: string, args: string[]): Promise<string> {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, { stdio: ["ignore", "pipe", "ignore"] });
    let stdout = "";
    child.stdout.on("data", (chunk) => (stdout += String(chunk)));
    child.on("error", reject);
    child.on("close", (code) => (code === 0 || code === 1 ? resolve(stdout) : reject(new Error(`${command} exited ${code}`))));
  });
}

function parseRgLine(raw: string): { file: string; lineNumber: number; lineText: string } | undefined {
  const separator = raw.includes(":") ? ":" : "-";
  const parts = raw.split(separator);
  if (parts.length < 3) return undefined;
  const file = parts[0] ?? "";
  const lineNumber = Number(parts[1]);
  const lineText = parts.slice(2).join(separator);
  return Number.isFinite(lineNumber) ? { file, lineNumber, lineText } : undefined;
}

function relativeTo(root: string, file: string): string {
  const relative = path.relative(path.resolve(root), path.resolve(file));
  return relative.startsWith("..") ? file : relative;
}
