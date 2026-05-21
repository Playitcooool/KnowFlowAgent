import fs from "node:fs/promises";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { IndexBuilder } from "../ingestion/indexBuilder.js";
import { KnowFlowWorkflow } from "../workflow.js";
import { defaultSettings } from "../config.js";

describe("KnowFlowWorkflow", () => {
  it("ingests markdown and answers with cited evidence", async () => {
    const root = await fs.mkdtemp(path.join(process.cwd(), ".tmp-knowflow-"));
    const markdownDir = path.join(root, "markdown");
    const kbDir = path.join(root, "knowledge_base");
    await fs.mkdir(markdownDir);
    await fs.writeFile(
      path.join(markdownDir, "reimbursement_policy.md"),
      `---\ntitle: Travel Reimbursement Policy\ntags: [finance, reimbursement, travel, approval]\n---\n# Travel Reimbursement Policy\n\nTravel reimbursement over 5000 yuan must be approved by the department manager and then reviewed by the finance manager.\n`,
      "utf8"
    );

    const manifest = await new IndexBuilder(kbDir).buildFromMarkdown(markdownDir);
    const answer = await new KnowFlowWorkflow({ ...defaultSettings, knowledgeBaseDir: kbDir, maxRetry: 3, minConfidence: 0.4 }).answerQuery(
      "Who approves travel reimbursement over 5000 yuan?"
    );

    expect(manifest.documents).toHaveLength(1);
    expect(answer.answerable).toBe(true);
    expect(answer.answer).toContain("department manager");
    expect(answer.citations.length).toBeGreaterThan(0);
    await fs.rm(root, { recursive: true, force: true });
  });
});
