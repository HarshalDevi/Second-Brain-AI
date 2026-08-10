import type {
  ChatResponse,
  DocumentRow,
  ChunkOut,
  ChunkRow,
  IngestJobOut,
} from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
const WORKSPACE_STORAGE_KEY = "secondbrain.workspaceId";

type StreamMeta = {
  conversation_id?: number | null;
  citations?: ChunkRow[];
};

function url(path: string) {
  return `${API_BASE}${path}`;
}

export function getWorkspaceId() {
  if (typeof window === "undefined") return "server-workspace";

  const existing = window.localStorage.getItem(WORKSPACE_STORAGE_KEY);
  if (existing) return existing;

  const id = `ws_${crypto.randomUUID().replaceAll("-", "")}`;
  window.localStorage.setItem(WORKSPACE_STORAGE_KEY, id);
  return id;
}

function workspaceHeaders(extra?: HeadersInit): HeadersInit {
  return {
    ...(extra ?? {}),
    "X-Workspace-Id": getWorkspaceId(),
  };
}

/* ----------------------------- Health ----------------------------- */

export async function health() {
  const r = await fetch(url("/health"));
  if (!r.ok) throw new Error(`Health failed: ${r.status}`);
  return r.json();
}

/* ----------------------------- Ingest ----------------------------- */

export async function ingestText(payload: { title: string; text: string }) {
  const r = await fetch(url("/v1/ingest/text"), {
    method: "POST",
    headers: workspaceHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload),
  });
  if (!r.ok) throw new Error(await r.text());
  return (await r.json()) as DocumentRow;
}

export async function ingestUrl(payload: { title: string; url: string }) {
  const r = await fetch(url("/v1/ingest/url"), {
    method: "POST",
    headers: workspaceHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload),
  });
  if (!r.ok) throw new Error(await r.text());
  return (await r.json()) as DocumentRow;
}

export async function ingestFile(file: File) {
  const fd = new FormData();
  fd.append("file", file);

  const r = await fetch(url("/v1/ingest/file"), {
    method: "POST",
    headers: workspaceHeaders(),
    body: fd,
  });
  if (!r.ok) throw new Error(await r.text());
  return (await r.json()) as DocumentRow;
}

export async function ingestAudio(file: File) {
  const fd = new FormData();
  fd.append("file", file);

  const r = await fetch(url("/v1/ingest/audio"), {
    method: "POST",
    headers: workspaceHeaders(),
    body: fd,
  });
  if (!r.ok) throw new Error(await r.text());
  return (await r.json()) as DocumentRow;
}

export async function jobStatus(documentId: number) {
  const r = await fetch(url(`/v1/ingest/jobs/${documentId}`), {
    headers: workspaceHeaders(),
  });
  if (!r.ok) throw new Error(await r.text());
  return (await r.json()) as IngestJobOut;
}

/* ----------------------------- Chat (non-stream) ----------------------------- */

export async function chat(payload: {
  query: string;
  conversation_id?: number | null;
}) {
  const r = await fetch(url("/v1/chat"), {
    method: "POST",
    headers: workspaceHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({
      query: payload.query,
      conversation_id: payload.conversation_id ?? null,
    }),
  });

  if (!r.ok) throw new Error(await r.text());
  return (await r.json()) as ChatResponse;
}

/* ----------------------------- Chat (streaming SSE) ----------------------------- */
export async function chatStream(
  payload: { query: string; conversation_id?: number | null },
  handlers: {
    onMeta?: (meta: StreamMeta | string) => void;
    onToken?: (token: string) => void;
    onDone?: () => void;
  }
) {
  const r = await fetch(url("/v1/chat/stream"), {
    method: "POST",
    headers: workspaceHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({
      query: payload.query,
      conversation_id: payload.conversation_id ?? null,
    }),
  });

  if (!r.ok) throw new Error(await r.text());
  if (!r.body) throw new Error("No response body for stream");

  const reader = r.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  const emit = (block: string) => {
    const lines = block.split("\n").map((l) => l.trimEnd());
    let eventName = "message";
    const dataLines: string[] = [];

    for (const line of lines) {
      if (line.startsWith("event:")) {
        eventName = line.slice(6).trim();
      } else if (line.startsWith("data:")) {
        dataLines.push(line.slice(5).trimStart());
      }
    }

    const data = dataLines.join("\n");

    if (eventName === "meta") {
      try {
        handlers.onMeta?.(JSON.parse(data));
      } catch {
        handlers.onMeta?.(data);
      }
      return;
    }

    if (eventName === "done") {
      handlers.onDone?.();
      return;
    }

    if (data) {
      try {
        const parsed = JSON.parse(data);
        if (typeof parsed?.token === "string") {
          handlers.onToken?.(parsed.token);
          return;
        }
      } catch {
        // Older backend streams raw token text.
      }
      handlers.onToken?.(data);
    }
  };

  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      let idx;
      while ((idx = buffer.indexOf("\n\n")) >= 0) {
        const block = buffer.slice(0, idx);
        buffer = buffer.slice(idx + 2);
        if (block.trim()) emit(block);
      }
    }

    if (buffer.trim()) emit(buffer);
  } finally {
    handlers.onDone?.();
  }
}

/* ----------------------------- Documents ----------------------------- */

export async function listDocuments() {
  const r = await fetch(url("/v1/documents"), {
    headers: workspaceHeaders(),
  });
  if (!r.ok) throw new Error(await r.text());
  return (await r.json()) as DocumentRow[];
}

export async function getDocumentChunks(documentId: number) {
  const r = await fetch(url(`/v1/documents/${documentId}/chunks`), {
    headers: workspaceHeaders(),
  });
  if (!r.ok) throw new Error(await r.text());
  return (await r.json()) as ChunkOut[];
}

export async function deleteDocument(documentId: number) {
  const r = await fetch(url(`/v1/documents/${documentId}`), {
    method: "DELETE",
    headers: workspaceHeaders(),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}