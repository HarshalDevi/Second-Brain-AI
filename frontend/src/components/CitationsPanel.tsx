"use client";

import type { ChunkRow } from "@/lib/types";

function citationTitle(citation: ChunkRow) {
  return citation.title || citation.doc_title || `Document ${citation.document_id}`;
}

function cleanCitationText(text: string) {
  return text
    .replace(/\[\s*\d+\s*\]/g, " ")
    .replace(/\s+/g, " ")
    .replace(/\s+([,.;:!?])/g, "$1")
    .trim();
}

function excerpt(text: string, maxLength = 360) {
  const cleaned = cleanCitationText(text);
  if (cleaned.length <= maxLength) return cleaned;

  const clipped = cleaned.slice(0, maxLength);
  const lastSpace = clipped.lastIndexOf(" ");
  return `${clipped.slice(0, lastSpace > 240 ? lastSpace : maxLength).trim()}...`;
}

function relevanceLabel(score?: number) {
  if (typeof score !== "number") return null;
  return `${Math.round(score * 100)}% match`;
}

export function CitationsPanel({ citations }: { citations: ChunkRow[] }) {
  const visibleCitations = citations.slice(0, 5);

  return (
    <section className="rounded-2xl bg-white p-4 ring-1 ring-slate-200">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-slate-950">Sources</h2>
          <p className="mt-1 text-xs text-slate-500">
            Evidence used for the latest answer
          </p>
        </div>
        <div className="shrink-0 rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
          {citations?.length ?? 0} chunks
        </div>
      </div>

      {!citations || citations.length === 0 ? (
        <div className="mt-3 rounded-xl bg-slate-50 p-3 text-sm text-slate-500 ring-1 ring-slate-200">
          No citations returned yet. Ingest content, then ask a question.
        </div>
      ) : (
        <div className="mt-3 grid gap-3">
          {visibleCitations.map((citation, index) => {
            const title = citationTitle(citation);
            const match = relevanceLabel(citation.score);
            const cleanedText = cleanCitationText(citation.text || "");

            return (
              <article
                key={`${citation.chunk_id}-${index}`}
                className="rounded-xl bg-slate-50 p-3 ring-1 ring-slate-200"
              >
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div className="min-w-0">
                    <div className="truncate text-sm font-medium text-slate-900">
                      {index + 1}. {title}
                    </div>
                    <div className="mt-1 flex flex-wrap gap-1.5 text-xs text-slate-500">
                      <span>doc {citation.document_id}</span>
                      <span aria-hidden="true">/</span>
                      <span>chunk {citation.chunk_index}</span>
                    </div>
                  </div>
                  {match && (
                    <span className="shrink-0 rounded-full bg-white px-2 py-1 text-xs font-medium text-slate-600 ring-1 ring-slate-300">
                      {match}
                    </span>
                  )}
                </div>

                <p className="mt-3 text-sm leading-6 text-slate-700">
                  {excerpt(citation.text || "")}
                </p>

                {cleanedText.length > 360 && (
                  <details className="mt-2 text-sm text-slate-700">
                    <summary className="cursor-pointer text-xs font-medium text-blue-700 hover:text-blue-800">
                      Show full chunk
                    </summary>
                    <p className="mt-2 whitespace-pre-wrap rounded-lg bg-white p-3 leading-6 ring-1 ring-slate-200">
                      {cleanedText}
                    </p>
                  </details>
                )}
              </article>
            );
          })}

          {citations.length > visibleCitations.length && (
            <div className="text-xs text-slate-500">
              Showing top {visibleCitations.length} of {citations.length} retrieved chunks.
            </div>
          )}
        </div>
      )}
    </section>
  );
}