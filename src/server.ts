import http from "node:http";
import { defaultSettings } from "./config.js";
import { DocumentConverter } from "./ingestion/converter.js";
import { IndexBuilder, loadManifest } from "./ingestion/indexBuilder.js";
import { KnowFlowWorkflow } from "./workflow.js";

export function createServer(settings = defaultSettings): http.Server {
  return http.createServer(async (req, res) => {
    try {
      if (req.method === "GET" && req.url === "/health") return json(res, { status: "ok" });
      if (req.method === "GET" && req.url === "/manifest") return json(res, await loadManifest(settings.knowledgeBaseDir));
      if (req.method === "POST" && req.url === "/ingest") {
        const body = await readJson(req);
        const runtime = {
          ...settings,
          rawDir: stringValue(body.rawDir ?? body.raw_dir, settings.rawDir),
          markdownDir: stringValue(body.markdownDir ?? body.markdown_dir, settings.markdownDir),
          knowledgeBaseDir: stringValue(body.knowledgeBaseDir ?? body.knowledge_base_dir, settings.knowledgeBaseDir)
        };
        await new DocumentConverter().convertDirectory(runtime.rawDir, runtime.markdownDir);
        return json(res, await new IndexBuilder(runtime.knowledgeBaseDir).buildFromMarkdown(runtime.markdownDir));
      }
      if (req.method === "POST" && req.url === "/query") {
        const body = await readJson(req);
        return json(res, await new KnowFlowWorkflow(settings).answerQuery(String(body.query ?? "")));
      }
      res.writeHead(404);
      res.end("Not found");
    } catch (error) {
      res.writeHead(500, { "content-type": "application/json" });
      res.end(JSON.stringify({ error: error instanceof Error ? error.message : String(error) }));
    }
  });
}

function json(res: http.ServerResponse, body: unknown): void {
  res.writeHead(200, { "content-type": "application/json" });
  res.end(JSON.stringify(body));
}

function stringValue(value: unknown, fallback: string): string {
  return typeof value === "string" && value ? value : fallback;
}

async function readJson(req: http.IncomingMessage): Promise<Record<string, unknown>> {
  const chunks: Buffer[] = [];
  for await (const chunk of req) chunks.push(Buffer.from(chunk));
  return chunks.length ? JSON.parse(Buffer.concat(chunks).toString("utf8")) : {};
}
