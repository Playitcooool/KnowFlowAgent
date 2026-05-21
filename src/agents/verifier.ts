import { type PiAgentClient } from "../piAgentClient.js";
import { citation, type Answer, type Evidence, type Verification } from "../types.js";
import { scoreText, tokenize } from "../textUtils.js";

export class VerifierAgent {
  constructor(private agent?: PiAgentClient) {}

  async verify(query: string, answer: Answer, evidence: Evidence[]): Promise<Verification> {
    if (this.agent?.available) {
      const verified = await this.piVerify(query, answer, evidence);
      if (verified) return verified;
    }
    return heuristicVerify(query, answer, evidence);
  }

  private async piVerify(query: string, answer: Answer, evidence: Evidence[]): Promise<Verification | undefined> {
    const result = await this.agent?.completeJson<{ answerable?: boolean; confidence?: number; missingInfo?: string[]; missing_info?: string[]; reason?: string }>(
      "Verify whether an answer is fully supported by evidence. Return only JSON with answerable, confidence, missingInfo, reason.",
      JSON.stringify({
        query,
        answer: answer.answer,
        citations: answer.citations,
        evidence: evidence.slice(0, 8).map((item) => `${citation(item)}\n${item.text}`).join("\n\n").slice(0, 10000)
      })
    );
    if (!result) return undefined;
    const confidence = Math.max(0, Math.min(1, Number(result.confidence ?? 0)));
    return {
      answerable: Boolean(result.answerable),
      confidence: Number(confidence.toFixed(4)),
      evidenceFiles: [...new Set(evidence.map((item) => item.file))].sort(),
      missingInfo: (result.missingInfo ?? result.missing_info ?? []).map(String),
      reason: result.reason ?? "Verified with Pi SDK."
    };
  }
}

function heuristicVerify(query: string, answer: Answer, evidence: Evidence[]): Verification {
  if (!evidence.length) {
    return { answerable: false, confidence: 0, evidenceFiles: [], missingInfo: ["No evidence was retrieved."], reason: "The retriever returned no matching Markdown evidence." };
  }
  const queryTerms = new Set(tokenize(query));
  const evidenceText = evidence.map((item) => item.text).join("\n");
  const coverage = scoreText(queryTerms, evidenceText);
  const bestScore = Math.max(...evidence.map((item) => item.score));
  const confidence = Math.min(1, coverage * 0.55 + bestScore * 0.45);
  const answerable = confidence >= 0.55 && answer.citations.length > 0;
  return {
    answerable,
    confidence: Number(confidence.toFixed(4)),
    evidenceFiles: [...new Set(evidence.map((item) => item.file))].sort(),
    missingInfo: answerable ? [] : ["Retrieved evidence does not cover enough query terms."],
    reason: "Evidence coverage and ranked retrieval score were used as the sufficiency signal."
  };
}
