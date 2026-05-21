import { type PiAgentClient } from "../piAgentClient.js";
import { citation, type Answer, type Evidence, type SearchTrace } from "../types.js";
import { tokenize } from "../textUtils.js";

export class AnswerAgent {
  constructor(private agent?: PiAgentClient) {}

  async generate(query: string, evidence: Evidence[], trace: SearchTrace[]): Promise<Answer> {
    if (!evidence.length) {
      return {
        query,
        answer: "I could not find enough evidence in the knowledge base to answer this. No cited document lines matched the question.",
        citations: [],
        confidence: 0,
        answerable: false,
        trace
      };
    }
    const llmAnswer = this.agent?.available ? await this.piAnswer(query, evidence.slice(0, 6)) : undefined;
    return {
      query,
      answer: llmAnswer || composeAnswer(query, evidence.slice(0, 4)),
      citations: evidence.slice(0, 4).map((item) => ({ file: item.file, lineStart: item.lineStart, lineEnd: item.lineEnd })),
      confidence: Math.max(...evidence.map((item) => item.score)),
      answerable: true,
      trace
    };
  }

  private async piAnswer(query: string, evidence: Evidence[]): Promise<string | undefined> {
    return this.agent?.complete(
      "You are a grounded enterprise knowledge QA agent. Answer only from the provided evidence. Cite file:line ranges inline. If evidence is insufficient, say what is missing.",
      `Question:\n${query}\n\nEvidence:\n${evidence.map((item, idx) => `[${idx + 1}] ${citation(item)}\n${item.text}`).join("\n\n")}`
    );
  }
}

function composeAnswer(query: string, evidence: Evidence[]): string {
  const queryTerms = new Set(tokenize(query));
  const sentences: string[] = [];
  for (const item of evidence) {
    const plain = item.text.replace(/^\d+:\s*/gm, "");
    for (const sentence of plain.split(/(?<=[.!?。！？])\s+|\n+/u)) {
      const cleaned = sentence.trim().replace(/^[-\t ]+/, "");
      if (!cleaned || cleaned.startsWith("#")) continue;
      if (tokenize(cleaned).some((term) => queryTerms.has(term))) sentences.push(cleaned);
      if (sentences.length >= 3) break;
    }
    if (sentences.length >= 3) break;
  }
  const body = sentences.length ? sentences.slice(0, 3).join(" ") : evidence[0]?.text.split(/\r?\n/)[0]?.replace(/^\d+:\s*/, "").trim() ?? "";
  return `${body}\n\nEvidence: ${evidence.slice(0, 3).map(citation).join("; ")}.`;
}
