"use client";

import type { ChunkRow } from "@/lib/types";

export function CitationsPanel({ citations }: { citations: ChunkRow[] }) {
  return (
    <div className="rounded-2xl bg-white p-4 ring-1 ring-slate-200">
      <div className="flex items-center justify-between">
        <div className="font-medium text-slate-900">Citations</div>
        <div className="text-xs text-slate-500">
          {citations?.length ?? 0} chunks
        </div>
      </div>

      {!citations || citations.length === 0 ? (
        <div className="mt-3 text-sm text-slate-500">
          No citations returned (ingest some content first).
        </div>
      ) : (
        <div className="mt-3 grid gap-3">
          {citations.map((c, i) => (
            <div
              key={`${c.chunk_id}-${i}`}
              className="rounded-xl bg-slate-50 p-3 ring-1 ring-slate-200"
            >
              <div className="flex flex-wrap items-center gap-2 text-xs text-slate-600">
                <span className="rounded-full bg-white px-2 py-1 ring-1 ring-slate-300">
                  doc {c.document_id}
                </span>
                <span className="rounded-full bg-white px-2 py-1 ring-1 ring-slate-300">
                  chunk {c.chunk_index}
                </span>
                {typeof c.score === "number" && (
                  <span className="rounded-full bg-white px-2 py-1 ring-1 ring-slate-300">
                    score {c.score.toFixed(3)}
                  </span>
                )}
                <span className="truncate text-xs text-slate-500">
                  {c.doc_title || ""}
                </span>
              </div>

              <div className="mt-2 whitespace-pre-wrap text-sm text-slate-800">
                {c.text}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}   