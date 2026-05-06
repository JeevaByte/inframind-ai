// Core domain types for InfraMind AI

/** Unique identifier type (UUID string) */
export type ID = string;

/** ISO 8601 datetime string */
export type ISODateString = string;

/** Semantic version string (e.g. "1.2.3") */
export type SemVer = string;

/** Generic paginated response wrapper */
export interface PaginatedResult<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
}

/** Standard API success envelope */
export interface ApiResponse<T = unknown> {
  success: true;
  data: T;
  meta?: Record<string, unknown>;
}

/** Standard API error envelope */
export interface ApiError {
  success: false;
  error: {
    code: string;
    message: string;
    details?: unknown;
  };
}

/** Either an API success or error */
export type ApiResult<T = unknown> = ApiResponse<T> | ApiError;

// ---------------------------------------------------------------------------
// User & Auth
// ---------------------------------------------------------------------------

export type UserRole = "admin" | "member" | "viewer";

export interface User {
  id: ID;
  email: string;
  name: string;
  role: UserRole;
  avatarUrl?: string;
  createdAt: ISODateString;
  updatedAt: ISODateString;
}

// ---------------------------------------------------------------------------
// Organisation / Workspace
// ---------------------------------------------------------------------------

export interface Organisation {
  id: ID;
  slug: string;
  name: string;
  plan: "free" | "pro" | "enterprise";
  createdAt: ISODateString;
  updatedAt: ISODateString;
}

// ---------------------------------------------------------------------------
// Infrastructure resources
// ---------------------------------------------------------------------------

export type ResourceStatus = "pending" | "running" | "stopped" | "failed" | "unknown";

export type CloudProvider = "aws" | "gcp" | "azure" | "hetzner" | "custom";

export interface Resource {
  id: ID;
  organisationId: ID;
  name: string;
  type: string;
  provider: CloudProvider;
  region: string;
  status: ResourceStatus;
  tags: Record<string, string>;
  metadata: Record<string, unknown>;
  createdAt: ISODateString;
  updatedAt: ISODateString;
}

// ---------------------------------------------------------------------------
// AI / Agent types
// ---------------------------------------------------------------------------

export type AgentStatus = "idle" | "thinking" | "executing" | "done" | "error";

export interface AgentMessage {
  id: ID;
  role: "user" | "assistant" | "system" | "tool";
  content: string;
  timestamp: ISODateString;
  metadata?: Record<string, unknown>;
}

export interface AgentSession {
  id: ID;
  organisationId: ID;
  userId: ID;
  status: AgentStatus;
  messages: AgentMessage[];
  createdAt: ISODateString;
  updatedAt: ISODateString;
}
