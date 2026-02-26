"use client";

import { useEffect, useState } from "react";
import { deleteDocument, getDocumentChunks, listDocuments } from "@/lib/api";
import type { ChunkOut, DocumentRow } from "@/lib/types";

export function DocumentsPanel() {
  const [docs, setDocs] = useState<DocumentRow[]>([]);
  const [selected, setSelected] = useState<DocumentRow | null>(null);
  const [chunks, setChunks] = useState<ChunkOut[]>([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function refresh() {
    setErr(null);
    setBusy(true);
    try {
      const d = await listDocuments();
      setDocs(d);
    } catch (e: any) {
      setErr(e?.message || String(e));
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function openDoc(doc: DocumentRow) {
    setSelected(doc);
    setChunks([]);
    setErr(null);
    try {
      const c = await getDocumentChunks(doc.id);
      setChunks(c);
    } catch (e: any) {
      setErr(e?.message || String(e));
    }
  }

  async function onDelete(doc: DocumentRow) {
    if (!confirm(`Delete doc ${doc.id} (${doc.title})?`)) return;
    setErr(null);
    try {
      await deleteDocument(doc.id);
      if (selected?.id === doc.id) {
        setSelected(null);
        setChunks([]);
      }
      await refresh();
    } catch (e: any) {
      setErr(e?.message || String(e));
    }
  }

  return (
    <div className="grid gap-4 md:grid-cols-2">
      <div className="rounded-2xl border bg-white p-4">
        <div className="flex items-center justify-between">
          <div className="font-medium">Documents</div>
          <button
            onClick={refresh}
            disabled={busy}
            className="rounded-xl border bg-white px-3 py-2 text-sm font-medium disabled:opacity-50"
          >
            Refresh
          </button>
        </div>

        {err && <div className="mt-3 rounded-xl bg-red-50 p-3 text-sm text-red-700">{err}</div>}

        <div className="mt-3 grid gap-2">
          {docs.length === 0 ? (
            <div className="text-sm text-zinc-500">No documents yet.</div>
          ) : (
            docs.map((d) => (
              <div key={d.id} className="rounded-xl border bg-zinc-50 p-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <div className="truncate text-sm font-medium">{d.title}</div>
                    <div className="mt-1 text-xs text-zinc-600">
                      id {d.id} • {d.source_type} • {d.status}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      className="rounded-lg bg-white border px-2 py-1 text-xs hover:bg-zinc-100"
                      onClick={() => openDoc(d)}
                    >
                      Open
                    </button>
                    <button
                      className="rounded-lg bg-white border px-2 py-1 text-xs text-red-700 hover:bg-red-50"
                      onClick={() => onDelete(d)}
                    >
                      Delete
                    </button>
                  </div>
                </div>
                {d.error && <div className="mt-2 text-xs text-red-700">{d.error}</div>}
              </div>
            ))
          )}
        </div>
      </div>

      <div className="rounded-2xl border bg-white p-4">
        <div className="font-medium">Chunks</div>
        {!selected ? (
          <div className="mt-3 text-sm text-zinc-500">Open a document to see its chunks.</div>
        ) : (
          <div className="mt-3">
            <div className="rounded-xl border bg-zinc-50 p-3 text-sm">
              <div className="truncate"><b>{selected.title}</b></div>
              <div className="mt-1 text-xs text-zinc-600">
                doc {selected.id} • {selected.source_type} • {selected.status}
              </div>
            </div>

            <div className="mt-3 grid gap-2">
              {chunks.length === 0 ? (
                <div className="text-sm text-zinc-500">No chunks yet (or still processing).</div>
              ) : (
                chunks.map((c) => (
                  <div key={c.id} className="rounded-xl border bg-zinc-50 p-3">
                    <div className="text-xs text-zinc-600">chunk {c.chunk_index}</div>
                    <div className="mt-2 whitespace-pre-wrap text-sm">{c.text}</div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}