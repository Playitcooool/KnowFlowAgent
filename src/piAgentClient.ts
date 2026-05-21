import { loadAppConfig, type AppConfig } from "./config.js";

export class PiAgentClient {
  private config?: AppConfig;

  constructor(configPath = "config.yaml") {
    this.config = loadAppConfig(configPath);
  }

  get available(): boolean {
    const provider = this.config?.provider;
    return Boolean(provider?.apiKeyEnv && process.env[provider.apiKeyEnv]);
  }

  async complete(systemPrompt: string, userPrompt: string): Promise<string | undefined> {
    if (!this.available) return undefined;
    try {
      const [{ createAgentSession, AuthStorage, ModelRegistry, SessionManager }, { getModel }] = await Promise.all([
        import("@earendil-works/pi-coding-agent"),
        import("@earendil-works/pi-ai")
      ]);
      const provider = this.config?.provider;
      if (!provider) return undefined;

      const authStorage = AuthStorage.create();
      authStorage.setRuntimeApiKey?.(provider.name, process.env[provider.apiKeyEnv] ?? "");
      const modelRegistry = ModelRegistry.create(authStorage);
      const model =
        (getModel as unknown as (provider: string, model: string) => unknown)(provider.name, provider.defaultModel) ??
        modelRegistry.find?.(provider.name, provider.defaultModel);

      let output = "";
      const { session } = await createAgentSession({
        authStorage,
        modelRegistry,
        model,
        noTools: "all",
        sessionManager: SessionManager.inMemory(),
        systemPrompt
      } as never);

      session.subscribe?.((event: unknown) => {
        const text = extractTextDelta(event);
        if (text) output += text;
      });

      const result = await session.prompt(userPrompt);
      return output.trim() || extractPromptResult(result)?.trim() || undefined;
    } catch {
      return undefined;
    }
  }

  async completeJson<T>(systemPrompt: string, userPrompt: string): Promise<T | undefined> {
    const text = await this.complete(systemPrompt, userPrompt);
    if (!text) return undefined;
    try {
      return JSON.parse(extractJson(text)) as T;
    } catch {
      return undefined;
    }
  }
}

function extractTextDelta(event: unknown): string {
  if (!event || typeof event !== "object") return "";
  const value = event as Record<string, unknown>;
  const assistant = value.assistantMessageEvent as Record<string, unknown> | undefined;
  if (value.type === "message_update" && assistant?.type === "text_delta") return String(assistant.delta ?? "");
  if (value.type === "text_delta") return String(value.delta ?? "");
  return "";
}

function extractPromptResult(result: unknown): string {
  if (typeof result === "string") return result;
  if (!result || typeof result !== "object") return "";
  const value = result as Record<string, unknown>;
  return String(value.text ?? value.content ?? "");
}

function extractJson(text: string): string {
  let stripped = text.trim();
  if (stripped.startsWith("```")) {
    const lines = stripped.split(/\r?\n/);
    if (lines[0]?.startsWith("```")) lines.shift();
    if (lines.at(-1)?.startsWith("```")) lines.pop();
    stripped = lines.join("\n").trim();
  }
  const objectStart = stripped.indexOf("{");
  const arrayStart = stripped.indexOf("[");
  const starts = [objectStart, arrayStart].filter((idx) => idx >= 0);
  const start = starts.length ? Math.min(...starts) : 0;
  const end = Math.max(stripped.lastIndexOf("}"), stripped.lastIndexOf("]"));
  return end >= start ? stripped.slice(start, end + 1) : stripped;
}
