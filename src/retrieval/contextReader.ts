import fs from "node:fs/promises";
import path from "node:path";
import { type Evidence, type GrepHit } from "../types.js";

export class ContextReader {
  constructor(private knowledgeBaseDir: string) {}

  async expand(hits: GrepHit[], windowSize = 20): Promise<Evidence[]> {
    const grouped = new Map<string, GrepHit[]>();
    for (const hit of hits) grouped.set(hit.file, [...(grouped.get(hit.file) ?? []), hit]);
    const evidence: Evidence[] = [];
    const radius = Math.max(1, Math.floor(windowSize / 2));
    for (const [file, fileHits] of grouped) {
      const filePath = path.join(this.knowledgeBaseDir, file);
      const lines = (await fs.readFile(filePath, "utf8")).split(/\r?\n/);
      const ranges = fileHits.map((hit) => ({
        start: Math.max(1, hit.lineNumber - radius),
        end: Math.min(lines.length, hit.lineNumber + radius),
        terms: new Set(hit.matchedTerms)
      }));
      for (const range of mergeRanges(ranges)) {
        evidence.push({
          file,
          lineStart: range.start,
          lineEnd: range.end,
          score: 0,
          matchedTerms: [...range.terms].sort(),
          text: Array.from({ length: range.end - range.start + 1 }, (_v, idx) => {
            const lineNo = range.start + idx;
            return `${lineNo}: ${lines[lineNo - 1] ?? ""}`;
          }).join("\n")
        });
      }
    }
    return evidence;
  }
}

function mergeRanges(ranges: Array<{ start: number; end: number; terms: Set<string> }>): Array<{ start: number; end: number; terms: Set<string> }> {
  const merged: Array<{ start: number; end: number; terms: Set<string> }> = [];
  for (const range of ranges.sort((a, b) => a.start - b.start)) {
    const last = merged.at(-1);
    if (!last || range.start > last.end + 1) merged.push({ start: range.start, end: range.end, terms: new Set(range.terms) });
    else {
      last.end = Math.max(last.end, range.end);
      for (const term of range.terms) last.terms.add(term);
    }
  }
  return merged;
}
