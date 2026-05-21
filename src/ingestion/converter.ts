import fs from "node:fs/promises";
import path from "node:path";
import fg from "fast-glob";

export class DocumentConverter {
  async convertDirectory(rawDir: string, markdownDir: string): Promise<string[]> {
    await fs.mkdir(markdownDir, { recursive: true });
    const files = await fg("**/*", { cwd: rawDir, onlyFiles: true, dot: false });
    const outputs: string[] = [];
    for (const file of files.sort()) {
      const source = path.join(rawDir, file);
      const output = path.join(markdownDir, `${path.parse(file).name}.md`);
      await this.convertFile(source, output);
      outputs.push(output);
    }
    return outputs;
  }

  async convertFile(source: string, output: string): Promise<string> {
    await fs.mkdir(path.dirname(output), { recursive: true });
    const ext = path.extname(source).toLowerCase();
    if (ext === ".md") {
      if (path.resolve(source) !== path.resolve(output)) await fs.copyFile(source, output);
    } else if (ext === ".txt" || ext === ".rst") {
      await fs.writeFile(output, await fs.readFile(source, "utf8"), "utf8");
    } else if (ext === ".html" || ext === ".htm") {
      await fs.writeFile(output, htmlToMarkdown(await fs.readFile(source, "utf8")), "utf8");
    } else if (ext === ".json") {
      await fs.writeFile(output, jsonToMarkdown(source, await fs.readFile(source, "utf8")), "utf8");
    } else {
      await fs.writeFile(output, await fs.readFile(source, "utf8"), "utf8");
    }
    return output;
  }
}

function htmlToMarkdown(text: string): string {
  return text
    .replace(/<\s*h([1-6])[^>]*>(.*?)<\s*\/\s*h\1\s*>/gis, (_match, level, content) => `${"#".repeat(Number(level))} ${stripTags(content)}`)
    .replace(/<br\s*\/?>/gi, "\n")
    .replace(/<\/p>/gi, "\n\n")
    .replace(/<[^>]+>/g, " ")
    .replace(/[ \t]+\n/g, "\n")
    .trim();
}

function stripTags(text: string): string {
  return text.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();
}

function jsonToMarkdown(source: string, text: string): string {
  const data = JSON.parse(text) as unknown;
  const title = path.basename(source, path.extname(source)).replace(/_/g, " ");
  if (Array.isArray(data)) {
    return [`# ${title}`, ...data.map((item, idx) => `\n## Item ${idx + 1}\n\n\`\`\`json\n${JSON.stringify(item, null, 2)}\n\`\`\``)].join("\n");
  }
  return `# ${title}\n\n\`\`\`json\n${JSON.stringify(data, null, 2)}\n\`\`\`\n`;
}
