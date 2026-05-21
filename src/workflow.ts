import fs from "node:fs";
import path from "node:path";
import { type Settings } from "./config.js";
import { PiAgentClient } from "./piAgentClient.js";
import { FileRouter } from "./agents/fileRouter.js";
import { QueryRouter } from "./agents/queryRouter.js";
import { QueryRewriter } from "./agents/queryRewriter.js";
import { AnswerAgent } from "./agents/answerAgent.js";
import { VerifierAgent } from "./agents/verifier.js";
import { loadManifest } from "./ingestion/indexBuilder.js";
import { GrepRetriever } from "./retrieval/grepRetriever.js";
import { ContextReader } from "./retrieval/contextReader.js";
import { EvidenceRanker } from "./retrieval/evidenceRanker.js";
import { type Answer, type SearchTrace } from "./types.js";

export class KnowFlowWorkflow {
  constructor(private settings: Settings) {}

  async answerQuery(query: string): Promise<Answer> {
    const manifest = await loadManifest(this.settings.knowledgeBaseDir);
    const agent = new PiAgentClient(this.settings.configPath);
    const queryRouter = new QueryRouter(this.settings.knowledgeBaseDir, manifest, agent);
    const fileRouter = new FileRouter(this.settings.knowledgeBaseDir, manifest, agent);
    const rewriter = new QueryRewriter(this.settings.knowledgeBaseDir, manifest, agent);
    const retriever = new GrepRetriever(this.settings.knowledgeBaseDir);
    const contextReader = new ContextReader(this.settings.knowledgeBaseDir);
    const ranker = new EvidenceRanker(manifest);
    const answerAgent = new AnswerAgent(agent);
    const verifier = new VerifierAgent(agent);

    const trace: SearchTrace[] = [];
    let bestAnswer: Answer | undefined;

    for (let retryLevel = 1; retryLevel <= this.settings.maxRetry; retryLevel += 1) {
      const route = await queryRouter.route(query, retryLevel);
      const targetFiles = await fileRouter.route(query, route.targetDirs, retryLevel);
      const targets = this.targets(route.targetDirs, targetFiles, retryLevel);
      const rewrittenQueries = await rewriter.rewrite(query, route.targetDirs, retryLevel < 3 ? 5 : 8, retryLevel);
      const hits = await retriever.search(rewrittenQueries, targets, this.settings.contextLines);
      const expanded = await contextReader.expand(hits, this.settings.expansionWindow);
      const evidence = ranker.rank(query, expanded, this.settings.topKEvidence);
      trace.push({ retryLevel, targetDirs: route.targetDirs, targetFiles, rewrittenQueries, evidenceCount: evidence.length, reason: route.reason });

      const answer = await answerAgent.generate(query, evidence, [...trace]);
      const verification = await verifier.verify(query, answer, evidence);
      const verifiedAnswer = { ...answer, confidence: verification.confidence, answerable: verification.answerable };
      if (!bestAnswer || verifiedAnswer.confidence > bestAnswer.confidence) bestAnswer = verifiedAnswer;
      if (verification.answerable && verification.confidence >= this.settings.minConfidence) return verifiedAnswer;
    }

    if (bestAnswer) {
      return {
        ...bestAnswer,
        answerable: false,
        answer: `${bestAnswer.answer}\n\nThe available evidence was not strong enough for a fully supported answer.`
      };
    }
    return { query, answer: "No searchable knowledge base was found.", citations: [], confidence: 0, answerable: false, trace };
  }

  private targets(targetDirs: string[], targetFiles: string[], retryLevel: number): string[] {
    if (retryLevel >= 4) return [this.settings.knowledgeBaseDir];
    const files = targetFiles.map((file) => path.join(this.settings.knowledgeBaseDir, file)).filter((file) => fs.existsSync(file));
    if (files.length && retryLevel <= 2) return files;
    const dirs = targetDirs.map((dir) => path.join(this.settings.knowledgeBaseDir, dir)).filter((dir) => fs.existsSync(dir));
    return dirs.length ? dirs : [this.settings.knowledgeBaseDir];
  }
}
