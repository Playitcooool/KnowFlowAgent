import fs from "node:fs";
import path from "node:path";
import { type PiAgentClient } from "../piAgentClient.js";
import { allCategories, type Manifest } from "../types.js";
import { scoreText, tokenize } from "../textUtils.js";

export class FileRouter {
  constructor(private knowledgeBaseDir: string, private manifest: Manifest, private agent?: PiAgentClient) {}

  async route(query: string, targetDirs: string[], retryLevel = 1): Promise<string[]> {
    if (this.agent?.available) {
      const files = await this.piRoute(query, targetDirs, retryLevel);
      if (files.length) return files;
    }
    return this.heuristicRoute(query, targetDirs, retryLevel);
  }

  private heuristicRoute(query: string, targetDirs: string[], retryLevel: number): string[] {
    const queryTerms = new Set(tokenize(query));
    const targetSet = new Set(targetDirs);
    const candidates: Array<[number, string]> = [];
    for (const doc of this.manifest.documents) {
      const firstPart = doc.path.split(/[\\/]/)[0];
      if (targetSet.has(firstPart ?? "") || [...allCategories(doc)].some((category) => targetSet.has(category))) {
        candidates.push([scoreText(queryTerms, [doc.title, doc.summary, ...doc.tags, ...doc.departments, doc.docType].join(" ")), doc.path]);
      }
    }
    if (!candidates.length) {
      for (const dir of targetDirs) {
        const folder = path.join(this.knowledgeBaseDir, dir);
        if (!fs.existsSync(folder)) continue;
        for (const file of fs.readdirSync(folder)) {
          if (file.endsWith(".md") && file !== "local_index.md") candidates.push([0, path.join(dir, file)]);
        }
      }
    }
    candidates.sort((a, b) => b[0] - a[0]);
    if (retryLevel >= 3) return candidates.map(([, file]) => file);
    return candidates.filter(([score]) => score > 0).slice(0, 6).map(([, file]) => file) || candidates.slice(0, 6).map(([, file]) => file);
  }

  private async piRoute(query: string, targetDirs: string[], retryLevel: number): Promise<string[]> {
    const candidates = this.manifest.documents
      .filter((doc) => {
        const firstPart = doc.path.split(/[\\/]/)[0];
        const categories = allCategories(doc);
        return !targetDirs.length || targetDirs.includes(firstPart ?? "") || targetDirs.some((dir) => categories.has(dir));
      })
      .map((doc) => ({ path: doc.path, title: doc.title, summary: doc.summary, tags: doc.tags, categories: [...allCategories(doc)] }));
    const result = await this.agent?.completeJson<{ targetFiles?: string[]; target_files?: string[] }>(
      "Select relevant Markdown files for a question. Return only JSON with targetFiles as candidate paths.",
      JSON.stringify({ query, retryLevel, targetDirs, candidateFiles: candidates.slice(0, 80) })
    );
    const allowed = new Set(candidates.map((item) => item.path));
    const files = (result?.targetFiles ?? result?.target_files ?? []).map(String).filter((file) => allowed.has(file));
    return retryLevel >= 3 ? files : files.slice(0, 6);
  }
}
