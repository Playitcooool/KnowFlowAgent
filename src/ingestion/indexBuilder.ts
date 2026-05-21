import fs from "node:fs/promises";
import path from "node:path";
import fg from "fast-glob";
import { MetadataExtractor } from "./metadata.js";
import { CATEGORY_KEYWORDS, slugify } from "../textUtils.js";
import { allCategories, type DocumentMetadata, type Manifest } from "../types.js";

export class IndexBuilder {
  private extractor = new MetadataExtractor();

  constructor(private knowledgeBaseDir: string) {}

  async buildFromMarkdown(markdownDir: string): Promise<Manifest> {
    await fs.mkdir(this.knowledgeBaseDir, { recursive: true });
    const documents: DocumentMetadata[] = [];
    const files = await fg("**/*.md", { cwd: markdownDir, onlyFiles: true });
    for (const file of files.sort()) {
      const source = path.join(markdownDir, file);
      const extracted = await this.extractor.extract(source, source);
      const category = slugify(extracted.primaryCategory);
      const target = path.join(this.knowledgeBaseDir, category, path.basename(source));
      await fs.mkdir(path.dirname(target), { recursive: true });
      if (path.resolve(source) !== path.resolve(target)) await fs.copyFile(source, target);
      documents.push({ ...extracted, path: path.relative(this.knowledgeBaseDir, target) });
    }
    const manifest = { documents };
    await this.writeIndexes(manifest);
    return manifest;
  }

  async writeIndexes(manifest: Manifest): Promise<void> {
    await fs.mkdir(this.knowledgeBaseDir, { recursive: true });
    const grouped = new Map<string, DocumentMetadata[]>();
    for (const doc of manifest.documents) {
      for (const category of allCategories(doc)) {
        grouped.set(category, [...(grouped.get(category) ?? []), doc]);
      }
    }
    for (const [category, docs] of grouped) {
      const folder = path.join(this.knowledgeBaseDir, category);
      await fs.mkdir(folder, { recursive: true });
      await fs.writeFile(path.join(folder, "local_index.md"), localIndex(category, docs), "utf8");
    }
    await fs.writeFile(path.join(this.knowledgeBaseDir, "index.md"), rootIndex(grouped), "utf8");
    await fs.writeFile(path.join(this.knowledgeBaseDir, "manifest.json"), JSON.stringify(manifest, null, 2), "utf8");
  }
}

export async function loadManifest(knowledgeBaseDir: string): Promise<Manifest> {
  try {
    return JSON.parse(await fs.readFile(path.join(knowledgeBaseDir, "manifest.json"), "utf8")) as Manifest;
  } catch {
    return { documents: [] };
  }
}

function rootIndex(grouped: Map<string, DocumentMetadata[]>): string {
  const lines = ["# Enterprise Knowledge Base Index", ""];
  for (const category of [...grouped.keys()].sort()) {
    const docs = grouped.get(category) ?? [];
    const summaries = docs.map((doc) => doc.summary).filter(Boolean).join(" ");
    const keywords = new Set([...(CATEGORY_KEYWORDS[category] ?? []), ...docs.flatMap((doc) => doc.tags)]);
    lines.push(`## ${category}`, "", summaries.slice(0, 500) || `Documents related to ${category}.`, "", `Typical keywords: ${[...keywords].sort().slice(0, 20).join(", ")}.`, "");
  }
  return lines.join("\n");
}

function localIndex(category: string, docs: DocumentMetadata[]): string {
  const lines = [`# ${category[0]?.toUpperCase() ?? ""}${category.slice(1)} Local Index`, ""];
  for (const doc of docs.sort((a, b) => a.path.localeCompare(b.path))) {
    lines.push(`## ${path.basename(doc.path)}`, doc.summary || doc.title, "");
  }
  return lines.join("\n");
}
