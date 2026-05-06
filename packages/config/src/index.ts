import { z } from "zod";

// ---------------------------------------------------------------------------
// Environment schemas — validate at startup so misconfiguration is caught
// immediately rather than at runtime.
// ---------------------------------------------------------------------------

/** Schema shared by all apps */
const baseEnvSchema = z.object({
  NODE_ENV: z.enum(["development", "test", "production"]).default("development"),
  LOG_LEVEL: z.enum(["debug", "info", "warn", "error"]).default("info"),
});

/** Additional fields required by the API server */
const apiEnvSchema = baseEnvSchema.extend({
  PORT: z.coerce.number().int().positive().default(3001),
  DATABASE_URL: z.string().url(),
  REDIS_URL: z.string().url().optional(),
  JWT_SECRET: z.string().min(32),
  OPENAI_API_KEY: z.string().startsWith("sk-").optional(),
  ANTHROPIC_API_KEY: z.string().optional(),
  CORS_ORIGIN: z.string().default("http://localhost:3000"),
});

/** Additional fields required by the web app */
const webEnvSchema = baseEnvSchema.extend({
  NEXT_PUBLIC_API_URL: z.string().url().default("http://localhost:3001"),
  NEXT_PUBLIC_APP_URL: z.string().url().default("http://localhost:3000"),
});

// ---------------------------------------------------------------------------
// Typed exports
// ---------------------------------------------------------------------------

export type BaseEnv = z.infer<typeof baseEnvSchema>;
export type ApiEnv = z.infer<typeof apiEnvSchema>;
export type WebEnv = z.infer<typeof webEnvSchema>;

/**
 * Parse and validate environment variables for the API server.
 * Throws a descriptive error on misconfiguration.
 */
export function parseApiEnv(env: NodeJS.ProcessEnv = process.env): ApiEnv {
  const result = apiEnvSchema.safeParse(env);
  if (!result.success) {
    throw new Error(
      `[config] Invalid API environment:\n${result.error.issues
        .map((i) => `  ${i.path.join(".")}: ${i.message}`)
        .join("\n")}`,
    );
  }
  return result.data;
}

/**
 * Parse and validate environment variables for the web app.
 * Throws a descriptive error on misconfiguration.
 */
export function parseWebEnv(env: NodeJS.ProcessEnv = process.env): WebEnv {
  const result = webEnvSchema.safeParse(env);
  if (!result.success) {
    throw new Error(
      `[config] Invalid Web environment:\n${result.error.issues
        .map((i) => `  ${i.path.join(".")}: ${i.message}`)
        .join("\n")}`,
    );
  }
  return result.data;
}
