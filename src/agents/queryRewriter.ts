import path from "node:path";
import fs from "node:fs";
import { type PiAgentClient } from "../piAgentClient.js";
import { allCategories, type Manifest } from "../types.js";
import { scoreText, tokenize, topTerms } from "../textUtils.js";

export class QueryRewriter {
  constructor(private knowledgeBaseDir: string, private manifest: Manifest, private agent?: PiAgentClient) {}

  async rewrite(query: string, targetDirs: string[] = [], n = 5, retryLevel = 1): Promise<string[]> {
    if (this.agent?.available) {
      const rewritten = await this.piRewrite(query, targetDirs, n, retryLevel);
      if (rewritten.length) return rewritten;
    }
    return this.heuristicRewrite(query, targetDirs, n, retryLevel);
  }

  private heuristicRewrite(query: string, targetDirs: string[], n: number, retryLevel: number): string[] {
    const terms = tokenize(query);
    const queries = [query];
    if (terms.length) queries.push(terms.join(" "));
    const contextTerms = this.contextTerms(query, targetDirs, retryLevel < 3 ? 12 : 20);
    if (contextTerms.length) {
      queries.push([...new Set([...terms, ...contextTerms.slice(0, 6)])].join(" "));
      queries.push(...contextTerms.slice(0, 3));
    }
    if (retryLevel >= 2) queries.push(...terms);
    if (retryLevel >= 3) queries.push(...contextTerms.slice(3, 8));
    if (retryLevel >= 4) queries.push(terms.slice(0, Math.max(1, Math.floor(terms.length / 2))).join(" "));
    return unique(queries).slice(0, n);
  }

  private async piRewrite(query: string, targetDirs: string[], n: number, retryLevel: number): Promise<string[]> {
    const result = await this.agent?.completeJson<string[]>(
      "Rewrite a question into concise keyword search queries for ripgrep over Markdown. Return only a JSON array of strings. Include the original query first.",
      JSON.stringify({
        query,
        targetDirs,
        retryLevel,
        maxQueries: n,
        manifestContext: this.manifestContext(targetDirs),
        indexContext: this.indexText(targetDirs).slice(0, 6000)
      })
    );
    if (!Array.isArray(result)) return [];
    return unique([query, ...result.map(String)]).slice(0, n);
  }

  private contextTerms(query: string, targetDirs: string[], limit: number): string[] {
    const queryTerms = new Set(tokenize(query));
    const ranked = this.manifestContext(targetDirs)
      .map((doc) => [scoreText(queryTerms, [doc.title, doc.summary, ...(doc.tags ?? [])].join(" ")), [doc.title, doc.summary, ...(doc.tags ?? [])].join(" ")] as const)
      .sort((a, b) => b[0] - a[0]);
    const sourceText = `${ranked.slice(0, 8).map(([, text]) => text).join(" ")} ${this.indexText(targetDirs)}`;
    return topTerms(sourceText, limit * 2).filter((term) => !queryTerms.has(term)).slice(0, limit);
  }

  private manifestContext(targetDirs: string[]): Array<{ path: string; title: string; summary: string; tags: string[]; categories: string[] }> {
    const targetSet = new Set(targetDirs);
    return this.manifest.documents
      .filter((doc) => {
        const firstPart = doc.path.split(/[\\/]/)[0];
        const categories = allCategories(doc);
        return !targetSet.size || targetSet.has(firstPart ?? "") || [...categories].some((category) => targetSet.has(category));
      })
      .slice(0, 80)
      .map((doc) => ({ path: doc.path, title: doc.title, summary: doc.summary, tags: doc.tags, categories: [...allCategories(doc)] }));
  }

  private indexText(targetDirs: string[]): string {
    return targetDirs.map((dir) => safeRead(path.join(this.knowledgeBaseDir, dir, "local_index.md"))).join("\n");
  }
}

function unique(values: string[]): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const value of values.map((item) => item.trim()).filter(Boolean)) {
    const key = value.toLowerCase();
    if (!seen.has(key)) {
      seen.add(key);
      out.push(value);
    }
  }
  return out;
}

function safeRead(file: string): string {
  try {
    return fs.readFileSync(file, "utf8");
  } catch {
    return "";
  }
}
