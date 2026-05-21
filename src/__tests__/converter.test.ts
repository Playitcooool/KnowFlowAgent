import fs from "node:fs/promises";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { DocumentConverter } from "../ingestion/converter.js";

describe("DocumentConverter", () => {
  it("allows markdown source and output paths to be identical", async () => {
    const root = await fs.mkdtemp(path.join(process.cwd(), ".tmp-converter-"));
    const markdownFile = path.join(root, "policy.md");
    await fs.writeFile(markdownFile, "# Policy\n\nUse this Markdown file.\n", "utf8");

    const outputs = await new DocumentConverter().convertDirectory(root, root);

    expect(outputs).toEqual([markdownFile]);
    expect(await fs.readFile(markdownFile, "utf8")).toContain("# Policy");
    await fs.rm(root, { recursive: true, force: true });
  });
});
