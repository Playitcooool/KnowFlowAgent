import fs from "node:fs";
import path from "node:path";
import { type PiAgentClient } from "../piAgentClient.js";
import { allCategories, type Manifest, type RouteDecision } from "../types.js";
import { scoreText, slugify, tokenize } from "../textUtils.js";

export class QueryRouter {
  constructor(private knowledgeBaseDir: string, private manifest: Manifest, private agent?: PiAgentClient) {}

  async route(query: string, retryLevel = 1): Promise<RouteDecision> {
    if (this.agent?.available) {
      const decision = await this.piRoute(query, retryLevel);
      if (decision.targetDirs.length) return decision;
    }
    return this.heuristicRoute(query, retryLevel);
  }

  private heuristicRoute(query: string, retryLevel: number): RouteDecision {
    const queryTerms = new Set(tokenize(query));
    const candidates = this.indexedDirs().map((folder) => {
      const text = this.readIndexText(folder);
      const scores = [scoreText(queryTerms, text)];
      for (const doc of this.manifest.documents) {
        if (allCategories(doc).has(folder) || doc.path.split(/[\\/]/)[0] === folder) {
          scores.push(scoreText(queryTerms, [doc.title, doc.summary, ...doc.tags].join(" ")));
        }
      }
      return [folder, Math.max(...scores)] as const;
    });
    const ranked = candidates.sort((a, b) => b[1] - a[1]);
    if (retryLevel >= 4) {
      return { targetDirs: ranked.map(([name]) => name), reason: "Full indexed-folder search because retry level requests a broader scope." };
    }
    const limit = retryLevel <= 1 ? 2 : 4;
    const dirs = ranked.filter(([, score]) => score > 0).slice(0, limit).map(([name]) => name);
    return {
      targetDirs: dirs.length ? dirs : ranked.slice(0, limit).map(([name]) => name),
      reason: "Selected folders from the root index by matching index text and manifest metadata."
    };
  }

  private async piRoute(query: string, retryLevel: number): Promise<RouteDecision> {
    const availableFolders = this.indexedDirs();
    const result = await this.agent?.completeJson<{ targetDirs?: string[]; target_dirs?: string[]; reason?: string }>(
      "Route a user question to knowledge-base folders. Return only JSON with targetDirs and reason. targetDirs must only contain names from availableFolders.",
      JSON.stringify({
        query,
        retryLevel,
        availableFolders,
        rootIndex: safeRead(path.join(this.knowledgeBaseDir, "index.md")).slice(0, 8000)
      })
    );
    const rawDirs = result?.targetDirs ?? result?.target_dirs ?? [];
    const allowed = new Set(availableFolders);
    const dirs = rawDirs.map(String).map(slugify).filter((dir) => allowed.has(dir));
    const limit = retryLevel >= 4 ? availableFolders.length : retryLevel <= 1 ? 2 : 4;
    return { targetDirs: dirs.slice(0, limit), reason: result?.reason ?? "Selected folders with Pi SDK router." };
  }

  private indexedDirs(): string[] {
    const indexPath = path.join(this.knowledgeBaseDir, "index.md");
    if (!fs.existsSync(indexPath)) return fallbackDirs(this.knowledgeBaseDir);
    const dirs = safeRead(indexPath)
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter((line) => line.startsWith("## ") && !line.startsWith("### "))
      .map((line) => slugify(line.replace(/^#+/, "").trim()));
    return [...new Set(dirs)].filter(Boolean);
  }

  private readIndexText(folder: string): string {
    return [folder, rootIndexSection(this.knowledgeBaseDir, folder), safeRead(path.join(this.knowledgeBaseDir, folder, "local_index.md"))].join("\n");
  }
}

function rootIndexSection(knowledgeBaseDir: string, folder: string): string {
  const lines = safeRead(path.join(knowledgeBaseDir, "index.md")).split(/\r?\n/);
  const out: string[] = [];
  let active = false;
  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith("## ") && !trimmed.startsWith("### ")) {
      if (active) break;
      active = slugify(trimmed.replace(/^#+/, "").trim()) === folder;
    }
    if (active) out.push(line);
  }
  return out.join("\n");
}

function fallbackDirs(dir: string): string[] {
  try {
    return fs.readdirSync(dir, { withFileTypes: true }).filter((entry) => entry.isDirectory()).map((entry) => entry.name).sort();
  } catch {
    return [];
  }
}

function safeRead(file: string): string {
  try {
    return fs.readFileSync(file, "utf8");
  } catch {
    return "";
  }
}
