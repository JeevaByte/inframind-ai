import type { ApiResponse, ApiError } from "../types/index.js";

// ---------------------------------------------------------------------------
// API response helpers
// ---------------------------------------------------------------------------

export function ok<T>(data: T, meta?: Record<string, unknown>): ApiResponse<T> {
  return { success: true, data, ...(meta !== undefined && { meta }) };
}

export function fail(
  code: string,
  message: string,
  details?: unknown,
): ApiError {
  return { success: false, error: { code, message, ...(details !== undefined && { details }) } };
}

// ---------------------------------------------------------------------------
// Type guards
// ---------------------------------------------------------------------------

export function isApiError(value: unknown): value is ApiError {
  return (
    typeof value === "object" &&
    value !== null &&
    "success" in value &&
    (value as ApiError).success === false
  );
}

// ---------------------------------------------------------------------------
// String utilities
// ---------------------------------------------------------------------------

export function slugify(value: string): string {
  return value
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, "")
    .replace(/[\s_-]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

export function truncate(value: string, maxLength: number, suffix = "..."): string {
  if (value.length <= maxLength) return value;
  return value.slice(0, maxLength - suffix.length) + suffix;
}

// ---------------------------------------------------------------------------
// Object utilities
// ---------------------------------------------------------------------------

/** Remove keys with undefined/null values from an object */
export function compact<T extends Record<string, unknown>>(obj: T): Partial<T> {
  return Object.fromEntries(
    Object.entries(obj).filter(([, v]) => v !== null && v !== undefined),
  ) as Partial<T>;
}

// ---------------------------------------------------------------------------
// Async utilities
// ---------------------------------------------------------------------------

export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function withRetry<T>(
  fn: () => Promise<T>,
  { retries = 3, delayMs = 200 }: { retries?: number; delayMs?: number } = {},
): Promise<T> {
  let lastError: unknown;
  for (let attempt = 0; attempt < retries; attempt++) {
    try {
      return await fn();
    } catch (err) {
      lastError = err;
      if (attempt < retries - 1) await sleep(delayMs * 2 ** attempt);
    }
  }
  throw lastError;
}
