import path from "node:path";

export const STOPWORDS = new Set([
  "a",
  "an",
  "and",
  "are",
  "as",
  "at",
  "be",
  "by",
  "do",
  "does",
  "for",
  "from",
  "how",
  "i",
  "if",
  "in",
  "is",
  "it",
  "my",
  "of",
  "on",
  "or",
  "the",
  "to",
  "what",
  "when",
  "where",
  "who",
  "with",
  "you",
  "your"
]);

export const CATEGORY_KEYWORDS: Record<string, Set<string>> = {
  hr: new Set(["employee", "onboarding", "leave", "benefit", "attendance", "performance", "salary"]),
  finance: new Set(["reimbursement", "expense", "invoice", "payment", "budget", "travel", "procurement", "approval"]),
  it: new Set(["account", "vpn", "device", "permission", "access", "ticket", "software", "github"]),
  engineering: new Set(["deploy", "deployment", "api", "code", "review", "database", "incident", "rollback", "repository"]),
  security: new Set(["security", "credential", "password", "access", "permission", "audit", "compliance"]),
  legal: new Set(["contract", "legal", "privacy", "terms", "compliance", "policy"])
};

export function slugify(value: string): string {
  const slug = value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9\u4e00-\u9fff]+/gu, "_")
    .replace(/_+/g, "_")
    .replace(/^_+|_+$/g, "");
  return slug || "document";
}

export function tokenize(text: string): string[] {
  return [...text.toLowerCase().matchAll(/[\w\u4e00-\u9fff]+/gu)]
    .map((match) => match[0])
    .filter((term) => term.length > 1 && !STOPWORDS.has(term));
}

export function topTerms(text: string, limit = 12): string[] {
  const counts = new Map<string, number>();
  for (const term of tokenize(text)) counts.set(term, (counts.get(term) ?? 0) + 1);
  return [...counts.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, limit)
    .map(([term]) => term);
}

export function scoreText(queryTerms: Set<string>, candidateText: string): number {
  if (!queryTerms.size) return 0;
  const candidateTerms = new Set(tokenize(candidateText));
  let overlap = 0;
  for (const term of queryTerms) if (candidateTerms.has(term)) overlap += 1;
  return overlap / queryTerms.size;
}

export function titleFromMarkdown(filePath: string, text: string): string {
  for (const line of text.split(/\r?\n/)) {
    const stripped = line.trim();
    if (stripped.startsWith("#")) return stripped.replace(/^#+/, "").trim() || titleFromPath(filePath);
  }
  return titleFromPath(filePath);
}

export function summarizeMarkdown(text: string, maxChars = 240): string {
  const lines: string[] = [];
  let inFrontMatter = false;
  const rawLines = text.split(/\r?\n/);
  rawLines.forEach((raw, idx) => {
    const line = raw.trim();
    if (idx === 0 && line === "---") {
      inFrontMatter = true;
      return;
    }
    if (inFrontMatter) {
      if (line === "---") inFrontMatter = false;
      return;
    }
    if (line && !line.startsWith("#") && !line.startsWith("|") && lines.join("").length <= maxChars) {
      lines.push(line.replace(/\s+/g, " "));
    }
  });
  return lines.join(" ").slice(0, maxChars).trimEnd();
}

export function inferCategories(text: string): string[] {
  const terms = new Set(tokenize(text));
  const scores = Object.entries(CATEGORY_KEYWORDS)
    .map(([category, keywords]) => [category, [...terms].filter((term) => keywords.has(term)).length] as const)
    .filter(([, score]) => score > 0)
    .sort((a, b) => b[1] - a[1]);
  return scores.map(([category]) => category) || ["general"];
}

function titleFromPath(filePath: string): string {
  return path.basename(filePath, path.extname(filePath)).replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}
