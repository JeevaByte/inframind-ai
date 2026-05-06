// Shared interface contracts used across apps and packages

import type { ID, ISODateString } from "../types/index.js";

/** Anything that can be serialised/deserialised */
export interface Serializable {
  toJSON(): Record<string, unknown>;
}

/** Repository pattern contract */
export interface Repository<T, CreateInput, UpdateInput> {
  findById(id: ID): Promise<T | null>;
  findAll(opts?: { page?: number; pageSize?: number }): Promise<T[]>;
  create(input: CreateInput): Promise<T>;
  update(id: ID, input: UpdateInput): Promise<T>;
  delete(id: ID): Promise<void>;
}

/** Generic event bus contract */
export interface EventBus {
  publish<T>(topic: string, payload: T): Promise<void>;
  subscribe<T>(topic: string, handler: (payload: T) => Promise<void>): () => void;
}

/** Logger interface (injected via DI) */
export interface Logger {
  debug(message: string, meta?: Record<string, unknown>): void;
  info(message: string, meta?: Record<string, unknown>): void;
  warn(message: string, meta?: Record<string, unknown>): void;
  error(message: string, error?: unknown, meta?: Record<string, unknown>): void;
}

/** Cache interface */
export interface Cache<T = unknown> {
  get(key: string): Promise<T | null>;
  set(key: string, value: T, ttlSeconds?: number): Promise<void>;
  delete(key: string): Promise<void>;
  flush(): Promise<void>;
}

/** AI provider contract */
export interface AIProvider {
  chat(messages: Array<{ role: string; content: string }>): Promise<string>;
  embed(text: string): Promise<number[]>;
}

/** Infrastructure provider contract */
export interface InfraProvider {
  listResources(region: string): Promise<unknown[]>;
  createResource(spec: unknown): Promise<{ id: string }>;
  deleteResource(id: string): Promise<void>;
}

/** Auditable entity */
export interface Auditable {
  createdAt: ISODateString;
  updatedAt: ISODateString;
  createdBy?: ID;
  updatedBy?: ID;
}
