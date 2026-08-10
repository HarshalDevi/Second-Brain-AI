"use client";

import { BookOpen, ChevronDown, FileText } from "lucide-react";
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

function excerpt(text: string, maxLength = 300) {
  const cleaned = cleanCitationText(text);
  if (cleaned.length <= maxLength) return cleaned;

  const clipped = cleaned.slice(0, maxLength);
  const lastSpace = clipped.lastIndexOf(" ");
  return `${clipped.slice(0, lastSpace > 220 ? lastSpace : maxLength).trim()}...`;
}

function relevanceLabel(score?: number) {
  if (typeof score !== "number") return null;
  return `${Math.round(score * 100)}%`;
}

export function CitationsPanel({ citations }: { citations: ChunkRow[] }) {
  const visibleCitations = citations.slice(0, 6);

  return (
    <aside className="rounded-2xl bg-white ring-1 ring-slate-200 xl:max-h-[720px] xl:overflow-hidden">
      <div className="flex items-center justify-between gap-3 border-b border-slate-200 px-4 py-3">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-50 text-emerald-700 ring-1 ring-emerald-100">
            <BookOpen className="h-5 w-5" aria-hidden="true" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-slate-950">Sources</h2>
            <p className="text-xs text-slate-500">Evidence for the latest answer</p>
          </div>
        </div>
        <div className="shrink-0 rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
          {citations?.length ?? 0} chunks
        </div>
      </div>

      {!citations || citations.length === 0 ? (
        <div className="p-4">
          <div className="rounded-2xl bg-slate-50 p-4 text-sm leading-6 text-slate-500 ring-1 ring-slate-200">
            Sources will appear here after a grounded answer is generated.
          </div>
        </div>
      ) : (
        <div className="grid gap-3 p-4 xl:max-h-[640px] xl:overflow-y-auto">
          {visibleCitations.map((citation, index) => {
            const title = citationTitle(citation);
            const match = relevanceLabel(citation.score);
            const cleanedText = cleanCitationText(citation.text || "");

            return (
              <article
                key={`${citation.chunk_id}-${index}`}
                className="rounded-2xl bg-slate-50 p-3 ring-1 ring-slate-200"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <FileText className="h-4 w-4 shrink-0 text-slate-400" aria-hidden="true" />
                      <div className="truncate text-sm font-semibold text-slate-900">
                        {index + 1}. {title}
                      </div>
                    </div>
                    <div className="mt-1 text-xs text-slate-500">
                      doc {citation.document_id} / chunk {citation.chunk_index}
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

                {cleanedText.length > 300 && (
                  <details className="group mt-2 text-sm text-slate-700">
                    <summary className="flex cursor-pointer list-none items-center gap-1 text-xs font-medium text-cyan-700 hover:text-cyan-800">
                      <ChevronDown className="h-3.5 w-3.5 transition group-open:rotate-180" aria-hidden="true" />
                      Full chunk
                    </summary>
                    <p className="mt-2 whitespace-pre-wrap rounded-xl bg-white p-3 leading-6 ring-1 ring-slate-200">
                      {cleanedText}
                    </p>
                  </details>
                )}
              </article>
            );
          })}

          {citations.length > visibleCitations.length && (
            <div className="rounded-xl bg-slate-50 px-3 py-2 text-xs text-slate-500 ring-1 ring-slate-200">
              Showing top {visibleCitations.length} of {citations.length} retrieved chunks.
            </div>
          )}
        </div>
      )}
    </aside>
  );
}