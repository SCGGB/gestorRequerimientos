/*
 * Cliente HTTP del frontend. Unico punto de acceso a la API.
 * La base es relativa (`/api/v1`): en desarrollo la resuelve el proxy de Vite
 * y en produccion el proxy de Nginx. No se embebe la URL interna del backend.
 */

const API_BASE = "/api/v1";

interface ErrorEnvelope {
  error?: {
    code?: string;
    message?: string;
    details?: unknown;
  };
}

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details: unknown;

  constructor(status: number, code: string, message: string, details: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export interface RequestOptions {
  method?: "GET" | "POST" | "PATCH" | "PUT" | "DELETE";
  body?: unknown;
  signal?: AbortSignal;
}

async function toApiError(response: Response): Promise<ApiError> {
  let code = "http_error";
  let message = `Error ${response.status}`;
  let details: unknown = null;
  try {
    const envelope = (await response.json()) as ErrorEnvelope;
    if (envelope.error !== undefined) {
      code = envelope.error.code ?? code;
      message = envelope.error.message ?? message;
      details = envelope.error.details ?? null;
    }
  } catch {
    // Cuerpo no JSON: se conservan los valores por defecto.
  }
  return new ApiError(response.status, code, message, details);
}

export async function request<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { method = "GET", body, signal } = options;
  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers:
      body === undefined ? undefined : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
    signal,
  });

  if (!response.ok) {
    throw await toApiError(response);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const text = await response.text();
  return (text === "" ? undefined : JSON.parse(text)) as T;
}
