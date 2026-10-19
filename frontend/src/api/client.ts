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
  const response = await send(path, options);

  if (!response.ok) {
    throw await toApiError(response);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const text = await response.text();
  return (text === "" ? undefined : JSON.parse(text)) as T;
}

export interface BlobResponse {
  blob: Blob;
  fileName: string;
}

export async function requestBlob(
  path: string,
  options: RequestOptions = {},
): Promise<BlobResponse> {
  const response = await send(path, options);

  if (!response.ok) {
    throw await toApiError(response);
  }

  return {
    blob: await response.blob(),
    fileName: fileNameFromDisposition(response.headers.get("Content-Disposition")),
  };
}

async function send(path: string, options: RequestOptions): Promise<Response> {
  const { method = "GET", body, signal } = options;
  return fetch(`${API_BASE}${path}`, {
    method,
    headers:
      body === undefined ? undefined : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
    signal,
  });
}

function fileNameFromDisposition(disposition: string | null): string {
  if (disposition === null) {
    return "documento";
  }
  const match = /filename\*?=(?:UTF-8'')?"?([^";]+)"?/i.exec(disposition);
  return match === null ? "documento" : decodeURIComponent(match[1]);
}
