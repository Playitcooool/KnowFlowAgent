import fs from "node:fs/promises";
import path from "node:path";
import { describe, expect, it, vi } from "vitest";
import { loadAppConfig } from "../config.js";
import { PiAgentClient } from "../piAgentClient.js";

describe("PiAgentClient config", () => {
  it("loads provider setup from config.yaml", async () => {
    const root = await fs.mkdtemp(path.join(process.cwd(), ".tmp-config-"));
    const configPath = path.join(root, "config.yaml");
    await fs.writeFile(
      configPath,
      `providers:\n  anthropic:\n    type: anthropic\n    api_key_env: ANTHROPIC_AUTH_TOKEN\n    base_url: https://api.example.com/anthropic\n    default_model: example-model\nruntime:\n  default_provider: anthropic\n  timeout_seconds: 12\n  max_retries: 2\n`,
      "utf8"
    );
    vi.stubEnv("ANTHROPIC_AUTH_TOKEN", "test-token");

    const config = loadAppConfig(configPath);
    const client = new PiAgentClient(configPath);

    expect(config?.provider?.name).toBe("anthropic");
    expect(config?.provider?.defaultModel).toBe("example-model");
    expect(client.available).toBe(true);
    vi.unstubAllEnvs();
    await fs.rm(root, { recursive: true, force: true });
  });
});
