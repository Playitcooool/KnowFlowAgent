import { allCategories, type Evidence, type Manifest } from "../types.js";
import { scoreText, tokenize } from "../textUtils.js";

export class EvidenceRanker {
  private metadataByPath = new Map<string, string>();

  constructor(manifest: Manifest = { documents: [] }) {
    for (const doc of manifest.documents) {
      this.metadataByPath.set(doc.path, [doc.title, doc.summary, ...doc.tags, ...allCategories(doc)].join(" "));
    }
  }

  rank(query: string, evidence: Evidence[], topK = 8): Evidence[] {
    const queryTerms = new Set(tokenize(query));
    return dedupe(evidence)
      .map((item) => {
        const keywordScore = scoreText(queryTerms, item.text);
        const coverageBonus = intersectionSize(new Set(item.matchedTerms), queryTerms) / Math.max(queryTerms.size, 1);
        const metadataBonus = scoreText(queryTerms, this.metadataByPath.get(item.file) ?? "");
        const score = Math.min(1, keywordScore * 0.65 + coverageBonus * 0.25 + metadataBonus * 0.1);
        return { ...item, score: Number(score.toFixed(4)) };
      })
      .sort((a, b) => b.score - a.score || b.matchedTerms.length - a.matchedTerms.length)
      .slice(0, topK);
  }
}

function dedupe(evidence: Evidence[]): Evidence[] {
  const seen = new Set<string>();
  return evidence.filter((item) => {
    const key = `${item.file}:${item.lineStart}:${item.lineEnd}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function intersectionSize(a: Set<string>, b: Set<string>): number {
  let count = 0;
  for (const item of a) if (b.has(item)) count += 1;
  return count;
}
