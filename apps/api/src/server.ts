import Fastify from "fastify";
import cors from "@fastify/cors";
import helmet from "@fastify/helmet";
import rateLimit from "@fastify/rate-limit";
import { parseApiEnv } from "@inframind/config";

const env = parseApiEnv();

export const app = Fastify({
  logger: {
    level: env.LOG_LEVEL,
    ...(env.NODE_ENV === "development" && {
      transport: { target: "pino-pretty", options: { colorize: true } },
    }),
  },
});

// ---------------------------------------------------------------------------
// Plugins
// ---------------------------------------------------------------------------

await app.register(helmet);
await app.register(cors, { origin: env.CORS_ORIGIN });
await app.register(rateLimit, { max: 100, timeWindow: "1 minute" });

// ---------------------------------------------------------------------------
// Health check
// ---------------------------------------------------------------------------

app.get("/health", async () => ({ status: "ok", version: process.env["npm_package_version"] }));

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------

try {
  await app.listen({ port: env.PORT, host: "0.0.0.0" });
} catch (err) {
  app.log.error(err);
  process.exit(1);
}
