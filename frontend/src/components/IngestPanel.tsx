"use client";

import { useState } from "react";
import { FileAudio, FileText, Globe2, Loader2, RefreshCw, Type, UploadCloud } from "lucide-react";
import { ingestAudio, ingestFile, ingestText, ingestUrl, jobStatus } from "@/lib/api";
import type { DocumentRow, IngestJobOut } from "@/lib/types";

const modes = [
  { id: "text", label: "Text", description: "Paste notes or snippets", icon: Type },
  { id: "url", label: "URL", description: "Clean article pages", icon: Globe2 },
  { id: "file", label: "File", description: "PDF and text documents", icon: FileText },
  { id: "audio", label: "Audio", description: "Transcribe recordings", icon: FileAudio },
] as const;

type Mode = (typeof modes)[number]["id"];

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : String(error);
}

function statusTone(status?: string) {
  if (status === "ready" || status === "done") return "bg-emerald-50 text-emerald-700 ring-emerald-100";
  if (status === "error" || status === "failed") return "bg-red-50 text-red-700 ring-red-100";
  return "bg-amber-50 text-amber-700 ring-amber-100";
}

export function IngestPanel() {
  const [mode, setMode] = useState<Mode>("text");
  const [title, setTitle] = useState("Daily Notes");
  const [text, setText] = useState("");
  const [url, setUrl] = useState("");
  const [file, setFile] = useState<File | null>(null);

  const [createdDoc, setCreatedDoc] = useState<DocumentRow | null>(null);
  const [job, setJob] = useState<IngestJobOut | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function onIngest() {
    setErr(null);
    setBusy(true);
    setCreatedDoc(null);
    setJob(null);

    try {
      let doc: DocumentRow;
      if (mode === "text") {
        if (!text.trim()) throw new Error("Paste text before ingesting.");
        doc = await ingestText({ title, text });
      } else if (mode === "url") {
        if (!url.trim()) throw new Error("Enter a URL before ingesting.");
        doc = await ingestUrl({ title, url });
      } else if (mode === "file") {
        if (!file) throw new Error("Pick a file first.");
        doc = await ingestFile(file);
      } else {
        if (!file) throw new Error("Pick an audio file first.");
        doc = await ingestAudio(file);
      }

      setCreatedDoc(doc);
      setJob(await jobStatus(doc.id));
    } catch (e: unknown) {
      setErr(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }

  async function onRefreshJob() {
    if (!createdDoc) return;
    setErr(null);
    try {
      setJob(await jobStatus(createdDoc.id));
    } catch (e: unknown) {
      setErr(errorMessage(e));
    }
  }

  return (
    <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_360px]">
      <section className="rounded-2xl bg-white p-4 ring-1 ring-slate-200">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {modes.map((item) => {
            const Icon = item.icon;
            const active = mode === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setMode(item.id)}
                className={[
                  "min-h-24 rounded-2xl p-3 text-left transition ring-1",
                  active
                    ? "bg-slate-950 text-white ring-slate-950"
                    : "bg-slate-50 text-slate-700 ring-slate-200 hover:bg-white",
                ].join(" ")}
              >
                <div
                  className={[
                    "flex h-9 w-9 items-center justify-center rounded-xl ring-1",
                    active
                      ? "bg-white/10 text-white ring-white/15"
                      : "bg-white text-cyan-700 ring-slate-200",
                  ].join(" ")}
                >
                  <Icon className="h-4 w-4" aria-hidden="true" />
                </div>
                <div className="mt-3 text-sm font-semibold">{item.label}</div>
                <div className={active ? "mt-1 text-xs text-slate-300" : "mt-1 text-xs text-slate-500"}>
                  {item.description}
                </div>
              </button>
            );
          })}
        </div>

        <div className="mt-5 grid gap-4">
          <label className="grid gap-1.5">
            <span className="text-xs font-medium uppercase tracking-[0.12em] text-slate-500">Title</span>
            <input
              className="h-11 rounded-xl bg-slate-50 px-3 text-sm text-slate-900 ring-1 ring-slate-200 outline-none focus:bg-white focus:ring-2 focus:ring-cyan-500"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="Document title"
            />
          </label>

          {mode === "text" && (
            <label className="grid gap-1.5">
              <span className="text-xs font-medium uppercase tracking-[0.12em] text-slate-500">Text</span>
              <textarea
                className="min-h-[280px] rounded-2xl bg-slate-50 px-3 py-3 text-sm leading-6 text-slate-900 ring-1 ring-slate-200 outline-none focus:bg-white focus:ring-2 focus:ring-cyan-500"
                value={text}
                onChange={(event) => setText(event.target.value)}
                placeholder="Paste notes, article text, meeting notes, or research snippets..."
              />
            </label>
          )}

          {mode === "url" && (
            <label className="grid gap-1.5">
              <span className="text-xs font-medium uppercase tracking-[0.12em] text-slate-500">URL</span>
              <input
                className="h-12 rounded-xl bg-slate-50 px-3 text-sm text-slate-900 ring-1 ring-slate-200 outline-none focus:bg-white focus:ring-2 focus:ring-cyan-500"
                value={url}
                onChange={(event) => setUrl(event.target.value)}
                placeholder="https://example.com/article"
              />
            </label>
          )}

          {(mode === "file" || mode === "audio") && (
            <label className="flex min-h-44 cursor-pointer flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-center hover:bg-white">
              <UploadCloud className="h-8 w-8 text-cyan-700" aria-hidden="true" />
              <span className="mt-3 text-sm font-medium text-slate-900">
                {file?.name ?? (mode === "audio" ? "Choose an audio file" : "Choose a document")}
              </span>
              <span className="mt-1 text-xs text-slate-500">
                {file ? `${Math.ceil(file.size / 1024)} KB selected` : "Click to browse from your computer"}
              </span>
              <input
                type="file"
                className="sr-only"
                accept={mode === "audio" ? "audio/*" : undefined}
                onChange={(event) => setFile(event.target.files?.[0] ?? null)}
              />
            </label>
          )}

          {err && (
            <div className="rounded-2xl bg-red-50 p-3 text-sm text-red-700 ring-1 ring-red-100">
              {err}
            </div>
          )}

          <div className="flex flex-wrap gap-2">
            <button
              disabled={busy}
              onClick={onIngest}
              className="inline-flex h-11 items-center gap-2 rounded-xl bg-cyan-600 px-4 text-sm font-semibold text-white hover:bg-cyan-700 disabled:cursor-not-allowed disabled:bg-slate-300"
            >
              {busy ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> : <UploadCloud className="h-4 w-4" aria-hidden="true" />}
              {busy ? "Ingesting" : "Ingest source"}
            </button>
            <button
              disabled={!createdDoc}
              onClick={onRefreshJob}
              className="inline-flex h-11 items-center gap-2 rounded-xl bg-white px-4 text-sm font-semibold text-slate-700 ring-1 ring-slate-200 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <RefreshCw className="h-4 w-4" aria-hidden="true" />
              Refresh status
            </button>
          </div>
        </div>
      </section>

      <aside className="rounded-2xl bg-white p-4 ring-1 ring-slate-200">
        <div className="text-sm font-semibold text-slate-950">Ingestion status</div>
        <p className="mt-1 text-sm leading-6 text-slate-500">
          Track the latest source as it moves through extract, chunk, embed, and store.
        </p>

        {!createdDoc ? (
          <div className="mt-4 rounded-2xl bg-slate-50 p-4 text-sm text-slate-500 ring-1 ring-slate-200">
            No source submitted in this session.
          </div>
        ) : (
          <div className="mt-4 grid gap-3 text-sm">
            <div className="rounded-2xl bg-slate-50 p-3 ring-1 ring-slate-200">
              <div className="text-xs text-slate-500">Document</div>
              <div className="mt-1 truncate font-semibold text-slate-950">{createdDoc.title || `Document ${createdDoc.id}`}</div>
              <div className="mt-2 flex flex-wrap gap-2 text-xs text-slate-500">
                <span>doc {createdDoc.id}</span>
                <span>{createdDoc.source_type}</span>
              </div>
            </div>

            <div className="rounded-2xl bg-slate-50 p-3 ring-1 ring-slate-200">
              <div className="text-xs text-slate-500">Document status</div>
              <span className={`mt-2 inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ${statusTone(createdDoc.status)}`}>
                {createdDoc.status}
              </span>
              {createdDoc.error && <div className="mt-2 text-sm text-red-700">{createdDoc.error}</div>}
            </div>

            {job && (
              <div className="rounded-2xl bg-slate-50 p-3 ring-1 ring-slate-200">
                <div className="text-xs text-slate-500">Pipeline</div>
                <div className="mt-2 flex items-center justify-between gap-3">
                  <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ${statusTone(job.status)}`}>
                    {job.status}
                  </span>
                  <span className="text-xs font-medium text-slate-600">{job.stage ?? "queued"}</span>
                </div>
                {job.error && <div className="mt-2 text-sm text-red-700">{job.error}</div>}
              </div>
            )}
          </div>
        )}
      </aside>
    </div>
  );
}