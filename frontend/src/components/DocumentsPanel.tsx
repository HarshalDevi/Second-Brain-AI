"use client";

import { useEffect, useMemo, useState } from "react";
import { FileText, Loader2, RefreshCw, Search, Trash2 } from "lucide-react";
import { deleteDocument, getDocumentChunks, listDocuments } from "@/lib/api";
import type { ChunkOut, DocumentRow } from "@/lib/types";

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : String(error);
}

function statusClass(status: string) {
  if (status === "ready") return "bg-emerald-50 text-emerald-700 ring-emerald-100";
  if (status === "error") return "bg-red-50 text-red-700 ring-red-100";
  return "bg-amber-50 text-amber-700 ring-amber-100";
}

function cleanPreview(text: string, maxLength = 320) {
  const cleaned = text.replace(/\s+/g, " ").trim();
  if (cleaned.length <= maxLength) return cleaned;
  return `${cleaned.slice(0, maxLength).trim()}...`;
}

export function DocumentsPanel() {
  const [docs, setDocs] = useState<DocumentRow[]>([]);
  const [selected, setSelected] = useState<DocumentRow | null>(null);
  const [chunks, setChunks] = useState<ChunkOut[]>([]);
  const [busy, setBusy] = useState(false);
  const [loadingChunks, setLoadingChunks] = useState(false);
  const [query, setQuery] = useState("");
  const [err, setErr] = useState<string | null>(null);

  const filteredDocs = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return docs;
    return docs.filter((doc) =>
      [doc.title, doc.source_type, doc.status, doc.source_uri]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(q))
    );
  }, [docs, query]);

  async function refresh() {
    setErr(null);
    setBusy(true);
    try {
      const d = await listDocuments();
      setDocs(d);
    } catch (e: unknown) {
      setErr(errorMessage(e));
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
    setLoadingChunks(true);
    try {
      setChunks(await getDocumentChunks(doc.id));
    } catch (e: unknown) {
      setErr(errorMessage(e));
    } finally {
      setLoadingChunks(false);
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
    } catch (e: unknown) {
      setErr(errorMessage(e));
    }
  }

  return (
    <div className="grid gap-4 xl:grid-cols-[390px_minmax(0,1fr)]">
      <section className="rounded-2xl bg-white ring-1 ring-slate-200">
        <div className="flex items-center justify-between gap-3 border-b border-slate-200 px-4 py-3">
          <div>
            <div className="text-sm font-semibold text-slate-950">Documents</div>
            <div className="text-xs text-slate-500">{docs.length} sources indexed</div>
          </div>
          <button
            onClick={refresh}
            disabled={busy}
            className="inline-flex h-10 items-center gap-2 rounded-xl bg-slate-50 px-3 text-sm font-medium text-slate-700 ring-1 ring-slate-200 hover:bg-slate-100 disabled:opacity-50"
          >
            {busy ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> : <RefreshCw className="h-4 w-4" aria-hidden="true" />}
            Refresh
          </button>
        </div>

        <div className="p-4">
          <label className="flex h-11 items-center gap-2 rounded-xl bg-slate-50 px-3 ring-1 ring-slate-200 focus-within:bg-white focus-within:ring-2 focus-within:ring-cyan-500">
            <Search className="h-4 w-4 text-slate-400" aria-hidden="true" />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search documents..."
              className="min-w-0 flex-1 bg-transparent text-sm outline-none placeholder:text-slate-400"
            />
          </label>

          {err && (
            <div className="mt-3 rounded-2xl bg-red-50 p-3 text-sm text-red-700 ring-1 ring-red-100">
              {err}
            </div>
          )}

          <div className="mt-3 grid max-h-[620px] gap-2 overflow-y-auto pr-1">
            {filteredDocs.length === 0 ? (
              <div className="rounded-2xl bg-slate-50 p-4 text-sm text-slate-500 ring-1 ring-slate-200">
                No documents match this filter.
              </div>
            ) : (
              filteredDocs.map((doc) => {
                const active = selected?.id === doc.id;
                return (
                  <article
                    key={doc.id}
                    className={[
                      "rounded-2xl p-3 ring-1 transition",
                      active
                        ? "bg-cyan-50 ring-cyan-200"
                        : "bg-slate-50 ring-slate-200 hover:bg-white",
                    ].join(" ")}
                  >
                    <button className="w-full text-left" onClick={() => openDoc(doc)}>
                      <div className="flex items-start gap-3">
                        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-white text-cyan-700 ring-1 ring-slate-200">
                          <FileText className="h-4 w-4" aria-hidden="true" />
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="truncate text-sm font-semibold text-slate-950">
                            {doc.title || `Document ${doc.id}`}
                          </div>
                          <div className="mt-1 flex flex-wrap gap-2 text-xs text-slate-500">
                            <span>doc {doc.id}</span>
                            <span>{doc.source_type}</span>
                            <span className={`rounded-full px-2 py-0.5 font-medium ring-1 ${statusClass(doc.status)}`}>
                              {doc.status}
                            </span>
                          </div>
                        </div>
                      </div>
                    </button>
                    <div className="mt-3 flex justify-end">
                      <button
                        className="inline-flex h-8 items-center gap-1.5 rounded-lg bg-white px-2 text-xs font-medium text-red-700 ring-1 ring-red-100 hover:bg-red-50"
                        onClick={() => onDelete(doc)}
                      >
                        <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
                        Delete
                      </button>
                    </div>
                    {doc.error && <div className="mt-2 text-xs text-red-700">{doc.error}</div>}
                  </article>
                );
              })
            )}
          </div>
        </div>
      </section>

      <section className="rounded-2xl bg-white ring-1 ring-slate-200">
        <div className="border-b border-slate-200 px-4 py-3">
          <div className="text-sm font-semibold text-slate-950">Chunk inspector</div>
          <div className="text-xs text-slate-500">
            {selected ? `${selected.title || `Document ${selected.id}`} / ${chunks.length} chunks` : "Open a document to inspect chunk quality"}
          </div>
        </div>

        <div className="max-h-[720px] overflow-y-auto p-4">
          {!selected ? (
            <div className="rounded-2xl bg-slate-50 p-6 text-center text-sm leading-6 text-slate-500 ring-1 ring-slate-200">
              Choose a document from the library to inspect its stored chunks and verify retrieval quality.
            </div>
          ) : loadingChunks ? (
            <div className="flex min-h-56 items-center justify-center text-sm text-slate-500">
              <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />
              Loading chunks
            </div>
          ) : chunks.length === 0 ? (
            <div className="rounded-2xl bg-slate-50 p-6 text-center text-sm text-slate-500 ring-1 ring-slate-200">
              No chunks yet. The ingestion pipeline may still be processing.
            </div>
          ) : (
            <div className="grid gap-3">
              {chunks.map((chunk) => (
                <article key={chunk.id} className="rounded-2xl bg-slate-50 p-3 ring-1 ring-slate-200">
                  <div className="flex items-center justify-between gap-3">
                    <div className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">
                      Chunk {chunk.chunk_index}
                    </div>
                    <div className="text-xs text-slate-400">{cleanPreview(chunk.text, 1_000).length} chars shown</div>
                  </div>
                  <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-700">
                    {cleanPreview(chunk.text, 1_000)}
                  </p>
                </article>
              ))}
            </div>
          )}
        </div>
      </section>
    </div>
  );
}