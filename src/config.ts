import fs from "node:fs";
import { parse } from "yaml";

export interface ProviderConfig {
  name: string;
  type: "openai_compatible" | "anthropic" | string;
  apiKeyEnv: string;
  baseUrl: string;
  defaultModel: string;
}

export interface RuntimeConfig {
  defaultProvider: string;
  timeoutSeconds: number;
  maxRetries: number;
}

export interface AppConfig {
  provider?: ProviderConfig;
  runtime: RuntimeConfig;
}

export interface Settings {
  knowledgeBaseDir: string;
  rawDir: string;
  markdownDir: string;
  configPath: string;
  maxRetry: number;
  contextLines: number;
  expansionWindow: number;
  topKEvidence: number;
  minConfidence: number;
}

export const defaultSettings: Settings = {
  knowledgeBaseDir: "knowledge_base",
  rawDir: "data/raw",
  markdownDir: "data/markdown",
  configPath: "config.yaml",
  maxRetry: 5,
  contextLines: 5,
  expansionWindow: 20,
  topKEvidence: 8,
  minConfidence: 0.55
};

export function loadAppConfig(configPath = "config.yaml"): AppConfig | undefined {
  if (!fs.existsSync(configPath)) return undefined;
  const raw = parse(fs.readFileSync(configPath, "utf8")) ?? {};
  const runtimeRaw = raw.runtime ?? {};
  const defaultProvider = String(runtimeRaw.default_provider ?? runtimeRaw.defaultProvider ?? "");
  const providerRaw = raw.providers?.[defaultProvider];
  const runtime: RuntimeConfig = {
    defaultProvider,
    timeoutSeconds: Number(runtimeRaw.timeout_seconds ?? runtimeRaw.timeoutSeconds ?? 60),
    maxRetries: Number(runtimeRaw.max_retries ?? runtimeRaw.maxRetries ?? 3)
  };
  if (!providerRaw) return { runtime };
  const apiKeyEnvRaw = providerRaw.api_key_env ?? providerRaw.apiKeyEnv ?? "";
  const apiKeyEnv = Array.isArray(apiKeyEnvRaw)
    ? String(apiKeyEnvRaw.find((name) => process.env[String(name)]) ?? apiKeyEnvRaw[0] ?? "")
    : String(apiKeyEnvRaw);
  return {
    runtime,
    provider: {
      name: defaultProvider,
      type: String(providerRaw.type ?? "openai_compatible"),
      apiKeyEnv,
      baseUrl: String(providerRaw.base_url ?? providerRaw.baseUrl ?? ""),
      defaultModel: String(providerRaw.default_model ?? providerRaw.defaultModel ?? "")
    }
  };
}
