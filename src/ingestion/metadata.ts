import crypto from "node:crypto";
import fs from "node:fs/promises";
import { type DocumentMetadata } from "../types.js";
import { inferCategories, slugify, summarizeMarkdown, titleFromMarkdown, topTerms } from "../textUtils.js";

export class MetadataExtractor {
  async extract(filePath: string, source?: string): Promise<DocumentMetadata> {
    const text = await fs.readFile(filePath, "utf8");
    const frontMatter = parseFrontMatter(text);
    const title = frontMatter.title ?? titleFromMarkdown(filePath, text);
    const summary = frontMatter.summary ?? summarizeMarkdown(text);
    const tags = listValue(frontMatter.tags) ?? topTerms(text, 10);
    const departments = listValue(frontMatter.departments) ?? [];
    const categories = listValue(frontMatter.categories) ?? inferCategories([title, summary, ...tags, text.slice(0, 4000)].join(" "));
    const primary = frontMatter.primary_category ?? categories[0] ?? "general";
    return {
      id: `doc_${crypto.createHash("sha1").update(filePath).digest("hex").slice(0, 12)}`,
      path: filePath,
      title,
      summary,
      tags,
      departments,
      docType: frontMatter.doc_type ?? "document",
      source: frontMatter.source ?? source,
      updatedAt: frontMatter.updated_at,
      primaryCategory: slugify(primary),
      secondaryCategories: categories.filter((category) => category !== primary).map(slugify)
    };
  }
}

function parseFrontMatter(text: string): Record<string, string> {
  const lines = text.split(/\r?\n/);
  if (lines[0]?.trim() !== "---") return {};
  const data: Record<string, string> = {};
  for (const line of lines.slice(1)) {
    if (line.trim() === "---") break;
    const idx = line.indexOf(":");
    if (idx > 0) data[line.slice(0, idx).trim()] = line.slice(idx + 1).trim().replace(/^['"]|['"]$/g, "");
  }
  return data;
}

function listValue(value?: string): string[] | undefined {
  if (!value) return undefined;
  const stripped = value.trim().replace(/^\[/, "").replace(/\]$/, "");
  const items = stripped.split(",").map((item) => item.trim().replace(/^['"]|['"]$/g, "")).filter(Boolean);
  return items.length ? items : undefined;
}
