// Application-wide constants

export const APP_NAME = "InfraMind AI";
export const APP_VERSION = "0.0.1";

// Pagination defaults
export const DEFAULT_PAGE_SIZE = 20;
export const MAX_PAGE_SIZE = 100;

// Token / rate limiting
export const MAX_AGENT_MESSAGES_PER_SESSION = 100;
export const MAX_TOKENS_PER_REQUEST = 8192;

// Cloud providers
export const CLOUD_PROVIDERS = ["aws", "gcp", "azure", "hetzner", "custom"] as const;

// Resource statuses
export const RESOURCE_STATUSES = [
  "pending",
  "running",
  "stopped",
  "failed",
  "unknown",
] as const;

// User roles
export const USER_ROLES = ["admin", "member", "viewer"] as const;

// HTTP status codes used throughout the API
export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  NO_CONTENT: 204,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  CONFLICT: 409,
  UNPROCESSABLE_ENTITY: 422,
  TOO_MANY_REQUESTS: 429,
  INTERNAL_SERVER_ERROR: 500,
  SERVICE_UNAVAILABLE: 503,
} as const;

// Error codes
export const ERROR_CODES = {
  VALIDATION_ERROR: "VALIDATION_ERROR",
  NOT_FOUND: "NOT_FOUND",
  UNAUTHORIZED: "UNAUTHORIZED",
  FORBIDDEN: "FORBIDDEN",
  CONFLICT: "CONFLICT",
  RATE_LIMITED: "RATE_LIMITED",
  INTERNAL_ERROR: "INTERNAL_ERROR",
} as const;
